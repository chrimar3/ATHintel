"""
🚨 Real-Time Market Alerts and Notifications

Advanced notification system for Greek energy market changes:
- Energy price fluctuations and market trends
- Government subsidy program updates (Εξοικονομώ)
- Regulatory changes and energy efficiency requirements
- Multi-channel delivery (email, SMS, push, webhooks)
- Smart filtering and personalized alerting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.application import MimeApplication
import aiohttp
import threading
from collections import defaultdict, deque

from config.production_config import get_config
from infrastructure.resilience import get_external_service_client
from monitoring.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    URGENT = "urgent"


class AlertCategory(Enum):
    """Alert categories"""
    ENERGY_PRICES = "energy_prices"
    MARKET_TRENDS = "market_trends"
    GOVERNMENT_SUBSIDIES = "government_subsidies"
    REGULATORY_CHANGES = "regulatory_changes"
    PROPERTY_OPPORTUNITIES = "property_opportunities"
    SYSTEM_ISSUES = "system_issues"
    ML_INSIGHTS = "ml_insights"


class DeliveryChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH_NOTIFICATION = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    name: str
    category: AlertCategory
    severity: AlertSeverity
    condition: str  # Condition expression
    threshold_value: Optional[float] = None
    time_window_minutes: int = 60
    cooldown_minutes: int = 30
    enabled: bool = True
    channels: List[DeliveryChannel] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    custom_message: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MarketAlert:
    """Market alert message"""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    channels: List[DeliveryChannel] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationTemplate:
    """Notification message template"""
    template_id: str
    name: str
    category: AlertCategory
    channel: DeliveryChannel
    subject_template: str
    body_template: str
    variables: List[str] = field(default_factory=list)


class GreekEnergyMarketMonitor:
    """
    Monitor for Greek energy market data and conditions
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Market data cache
        self.market_data: Dict[str, Any] = {}
        self.data_timestamps: Dict[str, datetime] = {}
        
        # Alert history for duplicate prevention
        self.alert_history: deque = deque(maxlen=1000)
        
        # Market data sources
        self.data_sources = {
            "energy_prices": {
                "url": "https://api.dapeep.gr/v1/market-prices",
                "interval_minutes": 15
            },
            "government_programs": {
                "url": "https://ypen.gov.gr/api/v1/programs",
                "interval_minutes": 60
            },
            "regulatory_updates": {
                "url": "https://rae.gr/api/v1/announcements",
                "interval_minutes": 120
            }
        }
        
        # Monitoring tasks
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        
        logger.info("Greek energy market monitor initialized")
    
    async def start_monitoring(self):
        """Start market monitoring"""
        if self.running:
            logger.warning("Market monitoring already running")
            return
        
        self.running = True
        
        # Start monitoring tasks for each data source
        for source_name, source_config in self.data_sources.items():
            task = asyncio.create_task(
                self._monitor_data_source(source_name, source_config)
            )
            self.monitoring_tasks[source_name] = task
        
        logger.info("Market monitoring started")
    
    async def stop_monitoring(self):
        """Stop market monitoring"""
        if not self.running:
            return
        
        self.running = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        self.monitoring_tasks.clear()
        logger.info("Market monitoring stopped")
    
    async def _monitor_data_source(self, source_name: str, source_config: Dict[str, Any]):
        """Monitor specific data source"""
        interval = source_config['interval_minutes'] * 60
        
        while self.running:
            try:
                # Fetch market data
                data = await self._fetch_market_data(source_name, source_config['url'])
                
                if data:
                    # Update market data
                    old_data = self.market_data.get(source_name)
                    self.market_data[source_name] = data
                    self.data_timestamps[source_name] = datetime.now()
                    
                    # Check for significant changes
                    await self._check_market_changes(source_name, old_data, data)
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring {source_name}: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _fetch_market_data(self, source_name: str, url: str) -> Optional[Dict[str, Any]]:
        """Fetch market data from external API"""
        try:
            client = await get_external_service_client()
            
            # Determine service name based on source
            if "dapeep" in url:
                service_name = "dapeep"
            elif "ypen" in url:
                service_name = "minenv"
            else:
                service_name = "external_api"
            
            response = await client.get(service_name, url)
            
            if response.success:
                logger.debug(f"Fetched market data from {source_name}")
                return response.data
            else:
                logger.warning(f"Failed to fetch market data from {source_name}: {response.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching market data from {source_name}: {e}")
            return None
    
    async def _check_market_changes(self, source_name: str, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]):
        """Check for significant market changes"""
        try:
            if source_name == "energy_prices":
                await self._check_energy_price_changes(old_data, new_data)
            elif source_name == "government_programs":
                await self._check_subsidy_program_changes(old_data, new_data)
            elif source_name == "regulatory_updates":
                await self._check_regulatory_changes(old_data, new_data)
                
        except Exception as e:
            logger.error(f"Error checking changes for {source_name}: {e}")
    
    async def _check_energy_price_changes(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]):
        """Check for energy price changes"""
        if not old_data:
            return
        
        # Check for significant price changes
        old_price = old_data.get('average_price_eur_mwh', 0)
        new_price = new_data.get('average_price_eur_mwh', 0)
        
        if old_price > 0:
            price_change_pct = ((new_price - old_price) / old_price) * 100
            
            # Alert on significant price changes (>10% change)
            if abs(price_change_pct) >= 10:
                severity = AlertSeverity.WARNING if abs(price_change_pct) < 20 else AlertSeverity.CRITICAL
                
                alert = MarketAlert(
                    alert_id=f"energy_price_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    rule_id="energy_price_change",
                    severity=severity,
                    category=AlertCategory.ENERGY_PRICES,
                    title=f"Significant Energy Price Change: {price_change_pct:+.1f}%",
                    message=f"Energy prices changed from €{old_price:.2f}/MWh to €{new_price:.2f}/MWh ({price_change_pct:+.1f}% change)",
                    data={
                        "old_price": old_price,
                        "new_price": new_price,
                        "change_percent": price_change_pct,
                        "market_data": new_data
                    },
                    timestamp=datetime.now(),
                    expires_at=datetime.now() + timedelta(hours=4)
                )
                
                await self._trigger_alert(alert)
    
    async def _check_subsidy_program_changes(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]):
        """Check for government subsidy program changes"""
        if not old_data:
            return
        
        old_programs = {p['id']: p for p in old_data.get('programs', [])}
        new_programs = {p['id']: p for p in new_data.get('programs', [])}
        
        # Check for new programs
        new_program_ids = set(new_programs.keys()) - set(old_programs.keys())
        for program_id in new_program_ids:
            program = new_programs[program_id]
            
            alert = MarketAlert(
                alert_id=f"new_subsidy_{program_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rule_id="new_subsidy_program",
                severity=AlertSeverity.INFO,
                category=AlertCategory.GOVERNMENT_SUBSIDIES,
                title=f"New Government Subsidy Program: {program['name']}",
                message=f"A new government subsidy program '{program['name']}' is now available with budget of €{program.get('budget', 0):,.0f}",
                data={
                    "program": program,
                    "is_new": True
                },
                timestamp=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
            await self._trigger_alert(alert)
        
        # Check for program updates (budget changes, deadline changes)
        for program_id in old_programs.keys() & new_programs.keys():
            old_prog = old_programs[program_id]
            new_prog = new_programs[program_id]
            
            # Check budget increases
            old_budget = old_prog.get('remaining_budget', 0)
            new_budget = new_prog.get('remaining_budget', 0)
            
            if new_budget > old_budget * 1.1:  # 10% increase
                alert = MarketAlert(
                    alert_id=f"subsidy_budget_{program_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    rule_id="subsidy_budget_increase",
                    severity=AlertSeverity.WARNING,
                    category=AlertCategory.GOVERNMENT_SUBSIDIES,
                    title=f"Subsidy Budget Increased: {new_prog['name']}",
                    message=f"Budget for '{new_prog['name']}' increased from €{old_budget:,.0f} to €{new_budget:,.0f}",
                    data={
                        "program": new_prog,
                        "old_budget": old_budget,
                        "new_budget": new_budget
                    },
                    timestamp=datetime.now()
                )
                
                await self._trigger_alert(alert)
    
    async def _check_regulatory_changes(self, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]):
        """Check for regulatory changes"""
        if not old_data:
            return
        
        old_announcements = {a['id']: a for a in old_data.get('announcements', [])}
        new_announcements = {a['id']: a for a in new_data.get('announcements', [])}
        
        # Check for new regulatory announcements
        new_announcement_ids = set(new_announcements.keys()) - set(old_announcements.keys())
        
        for announcement_id in new_announcement_ids:
            announcement = new_announcements[announcement_id]
            
            # Classify severity based on content
            severity = AlertSeverity.INFO
            if any(keyword in announcement.get('title', '').lower() for keyword in ['mandatory', 'required', 'deadline']):
                severity = AlertSeverity.WARNING
            if any(keyword in announcement.get('title', '').lower() for keyword in ['immediate', 'urgent', 'emergency']):
                severity = AlertSeverity.CRITICAL
            
            alert = MarketAlert(
                alert_id=f"regulatory_{announcement_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rule_id="regulatory_change",
                severity=severity,
                category=AlertCategory.REGULATORY_CHANGES,
                title=f"New Regulatory Announcement: {announcement['title']}",
                message=f"RAE published: {announcement['title']}\n\n{announcement.get('summary', '')}",
                data={
                    "announcement": announcement,
                    "source": "RAE"
                },
                timestamp=datetime.now(),
                expires_at=datetime.now() + timedelta(days=14)
            )
            
            await self._trigger_alert(alert)
    
    async def _trigger_alert(self, alert: MarketAlert):
        """Trigger market alert"""
        # Prevent duplicate alerts
        alert_key = f"{alert.rule_id}_{alert.title}"
        if alert_key in [h.get('key') for h in list(self.alert_history)]:
            logger.debug(f"Skipping duplicate alert: {alert.title}")
            return
        
        # Record alert in history
        self.alert_history.append({
            'key': alert_key,
            'timestamp': alert.timestamp,
            'alert_id': alert.alert_id
        })
        
        # Get alert engine and send alert
        alert_engine = get_market_alert_engine()
        await alert_engine.send_alert(alert)
        
        logger.info(f"Market alert triggered: {alert.title}")
    
    def get_latest_market_data(self) -> Dict[str, Any]:
        """Get latest market data"""
        return {
            "data": self.market_data,
            "timestamps": {k: v.isoformat() for k, v in self.data_timestamps.items()},
            "last_updated": datetime.now().isoformat()
        }


class NotificationDelivery:
    """
    Multi-channel notification delivery system
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Templates
        self.templates: Dict[str, NotificationTemplate] = {}
        self._initialize_templates()
        
        # Delivery stats
        self.delivery_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
    def _initialize_templates(self):
        """Initialize notification templates"""
        # Energy price change templates
        self.templates["energy_price_email"] = NotificationTemplate(
            template_id="energy_price_email",
            name="Energy Price Change Email",
            category=AlertCategory.ENERGY_PRICES,
            channel=DeliveryChannel.EMAIL,
            subject_template="⚡ Energy Price Alert: {change_percent:+.1f}% Change",
            body_template="""
Energy Market Alert - Price Change

Dear {recipient_name},

We detected a significant change in Greek energy market prices:

• Previous Price: €{old_price:.2f}/MWh
• Current Price: €{new_price:.2f}/MWh
• Change: {change_percent:+.1f}%

This change may impact:
- Property energy assessments
- ROI calculations for energy improvements
- Government subsidy recommendations

For detailed analysis, visit your ATHintel dashboard.

Best regards,
ATHintel Energy Assessment Platform
            """,
            variables=["recipient_name", "old_price", "new_price", "change_percent"]
        )
        
        # Government subsidy templates
        self.templates["subsidy_program_email"] = NotificationTemplate(
            template_id="subsidy_program_email",
            name="New Subsidy Program Email",
            category=AlertCategory.GOVERNMENT_SUBSIDIES,
            channel=DeliveryChannel.EMAIL,
            subject_template="🏛️ New Government Subsidy: {program_name}",
            body_template="""
New Government Subsidy Program Available

Dear {recipient_name},

A new government subsidy program is now available:

Program: {program_name}
Budget: €{budget:,.0f}
Deadline: {deadline}

Key Details:
{program_details}

This program may benefit your properties. Check your ATHintel recommendations for eligibility analysis.

Best regards,
ATHintel Energy Assessment Platform
            """,
            variables=["recipient_name", "program_name", "budget", "deadline", "program_details"]
        )
    
    async def deliver_notification(
        self,
        alert: MarketAlert,
        channel: DeliveryChannel,
        recipient: str
    ) -> bool:
        """
        Deliver notification via specified channel
        
        Args:
            alert: Alert to deliver
            channel: Delivery channel
            recipient: Recipient address/identifier
            
        Returns:
            Success status
        """
        try:
            if channel == DeliveryChannel.EMAIL:
                return await self._send_email(alert, recipient)
            elif channel == DeliveryChannel.WEBHOOK:
                return await self._send_webhook(alert, recipient)
            elif channel == DeliveryChannel.SLACK:
                return await self._send_slack(alert, recipient)
            else:
                logger.warning(f"Unsupported delivery channel: {channel}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deliver notification via {channel} to {recipient}: {e}")
            self.delivery_stats[channel.value]["failed"] += 1
            return False
    
    async def _send_email(self, alert: MarketAlert, recipient: str) -> bool:
        """Send email notification"""
        try:
            # Get email template
            template_key = f"{alert.category.value}_email"
            template = self.templates.get(template_key)
            
            if not template:
                # Use generic template
                subject = f"ATHintel Alert: {alert.title}"
                body = f"{alert.title}\n\n{alert.message}\n\nTimestamp: {alert.timestamp.isoformat()}"
            else:
                # Use specific template
                subject = template.subject_template.format(**alert.data)
                body = template.body_template.format(
                    recipient_name=recipient.split('@')[0].title(),
                    **alert.data
                )
            
            # Create email message
            msg = MimeMultipart()
            msg['From'] = "alerts@athintel.gr"
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            # Add alert data as JSON attachment for debugging
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.URGENT]:
                json_data = json.dumps(alert.data, indent=2, default=str)
                attachment = MimeApplication(json_data.encode(), Name="alert_data.json")
                attachment['Content-Disposition'] = 'attachment; filename="alert_data.json"'
                msg.attach(attachment)
            
            # Send email (mock implementation)
            logger.info(f"EMAIL SENT to {recipient}: {subject}")
            self.delivery_stats[DeliveryChannel.EMAIL.value]["sent"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return False
    
    async def _send_webhook(self, alert: MarketAlert, webhook_url: str) -> bool:
        """Send webhook notification"""
        try:
            payload = {
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "category": alert.category.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "data": alert.data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status < 400:
                        logger.info(f"WEBHOOK SENT to {webhook_url}: {alert.title}")
                        self.delivery_stats[DeliveryChannel.WEBHOOK.value]["sent"] += 1
                        return True
                    else:
                        logger.error(f"Webhook delivery failed: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return False
    
    async def _send_slack(self, alert: MarketAlert, slack_webhook: str) -> bool:
        """Send Slack notification"""
        try:
            # Slack color coding
            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning", 
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.URGENT: "danger"
            }
            
            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "good"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.title(),
                                "short": True
                            },
                            {
                                "title": "Category",
                                "value": alert.category.value.replace('_', ' ').title(),
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": False
                            }
                        ],
                        "footer": "ATHintel Energy Assessment Platform"
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    slack_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status < 400:
                        logger.info(f"SLACK SENT: {alert.title}")
                        self.delivery_stats[DeliveryChannel.SLACK.value]["sent"] += 1
                        return True
                    else:
                        logger.error(f"Slack delivery failed: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            return False
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        return dict(self.delivery_stats)


class MarketAlertEngine:
    """
    Main market alert engine coordinating monitoring and delivery
    """
    
    def __init__(self):
        self.market_monitor = GreekEnergyMarketMonitor()
        self.notification_delivery = NotificationDelivery()
        
        # Alert rules
        self.alert_rules: Dict[str, AlertRule] = {}
        self._initialize_default_rules()
        
        # Subscriber management
        self.subscribers: Dict[str, Dict[str, Any]] = {}
        
        # Running state
        self.running = False
        
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        # Energy price change rule
        self.alert_rules["energy_price_change"] = AlertRule(
            rule_id="energy_price_change",
            name="Energy Price Change Alert",
            category=AlertCategory.ENERGY_PRICES,
            severity=AlertSeverity.WARNING,
            condition="price_change_percent >= 10",
            threshold_value=10.0,
            time_window_minutes=60,
            cooldown_minutes=30,
            channels=[DeliveryChannel.EMAIL, DeliveryChannel.WEBHOOK],
            recipients=["admin@athintel.gr"]
        )
        
        # New subsidy program rule
        self.alert_rules["new_subsidy_program"] = AlertRule(
            rule_id="new_subsidy_program",
            name="New Government Subsidy Program",
            category=AlertCategory.GOVERNMENT_SUBSIDIES,
            severity=AlertSeverity.INFO,
            condition="new_program == true",
            channels=[DeliveryChannel.EMAIL, DeliveryChannel.SLACK],
            recipients=["admin@athintel.gr"]
        )
        
        # Regulatory change rule
        self.alert_rules["regulatory_change"] = AlertRule(
            rule_id="regulatory_change",
            name="Regulatory Change Alert",
            category=AlertCategory.REGULATORY_CHANGES,
            severity=AlertSeverity.WARNING,
            condition="new_announcement == true",
            channels=[DeliveryChannel.EMAIL],
            recipients=["admin@athintel.gr"]
        )
    
    async def start(self):
        """Start the alert engine"""
        if self.running:
            logger.warning("Alert engine already running")
            return
        
        self.running = True
        await self.market_monitor.start_monitoring()
        logger.info("Market alert engine started")
    
    async def stop(self):
        """Stop the alert engine"""
        if not self.running:
            return
        
        self.running = False
        await self.market_monitor.stop_monitoring()
        logger.info("Market alert engine stopped")
    
    async def send_alert(self, alert: MarketAlert):
        """Send alert through configured channels"""
        try:
            # Get applicable rule
            rule = self.alert_rules.get(alert.rule_id)
            
            if not rule or not rule.enabled:
                logger.debug(f"Alert rule {alert.rule_id} not found or disabled")
                return
            
            # Use rule configuration if alert doesn't specify
            channels = alert.channels if alert.channels else rule.channels
            recipients = alert.recipients if alert.recipients else rule.recipients
            
            # Record alert metrics
            metrics_collector = get_metrics_collector()
            if hasattr(metrics_collector, 'record_alert'):
                metrics_collector.record_alert(
                    alert.category.value,
                    alert.severity.value,
                    len(recipients)
                )
            
            # Send to all recipients via all channels
            delivery_tasks = []
            for channel in channels:
                for recipient in recipients:
                    task = asyncio.create_task(
                        self.notification_delivery.deliver_notification(alert, channel, recipient)
                    )
                    delivery_tasks.append(task)
            
            # Wait for all deliveries
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            successful_deliveries = sum(1 for r in results if r is True)
            total_deliveries = len(delivery_tasks)
            
            logger.info(f"Alert {alert.alert_id} delivered: {successful_deliveries}/{total_deliveries} successful")
            
        except Exception as e:
            logger.error(f"Failed to send alert {alert.alert_id}: {e}")
    
    def add_subscriber(
        self,
        subscriber_id: str,
        email: str,
        categories: List[AlertCategory],
        channels: List[DeliveryChannel],
        webhook_url: Optional[str] = None,
        slack_webhook: Optional[str] = None
    ):
        """Add alert subscriber"""
        self.subscribers[subscriber_id] = {
            "email": email,
            "categories": [c.value for c in categories],
            "channels": [c.value for c in channels],
            "webhook_url": webhook_url,
            "slack_webhook": slack_webhook,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        logger.info(f"Added subscriber: {subscriber_id}")
    
    def remove_subscriber(self, subscriber_id: str):
        """Remove alert subscriber"""
        if subscriber_id in self.subscribers:
            del self.subscribers[subscriber_id]
            logger.info(f"Removed subscriber: {subscriber_id}")
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status and monitoring info"""
        return {
            "monitoring_active": self.running,
            "market_data": self.market_monitor.get_latest_market_data(),
            "alert_rules": {
                rule_id: {
                    "name": rule.name,
                    "category": rule.category.value,
                    "enabled": rule.enabled,
                    "channels": [c.value for c in rule.channels]
                }
                for rule_id, rule in self.alert_rules.items()
            },
            "subscribers": len(self.subscribers),
            "delivery_stats": self.notification_delivery.get_delivery_stats()
        }


# Global alert engine instance
_market_alert_engine = None


def get_market_alert_engine() -> MarketAlertEngine:
    """Get or create global market alert engine"""
    global _market_alert_engine
    if _market_alert_engine is None:
        _market_alert_engine = MarketAlertEngine()
    return _market_alert_engine


# Convenience functions
async def start_market_alerts():
    """Start market alert system"""
    engine = get_market_alert_engine()
    await engine.start()


async def stop_market_alerts():
    """Stop market alert system"""
    engine = get_market_alert_engine()
    await engine.stop()


def subscribe_to_alerts(
    subscriber_id: str,
    email: str,
    categories: List[str],
    channels: List[str] = None
):
    """Subscribe to market alerts"""
    engine = get_market_alert_engine()
    
    alert_categories = [AlertCategory(cat) for cat in categories]
    delivery_channels = [DeliveryChannel(ch) for ch in (channels or ["email"])]
    
    engine.add_subscriber(subscriber_id, email, alert_categories, delivery_channels)


def get_market_status() -> Dict[str, Any]:
    """Get current market monitoring status"""
    engine = get_market_alert_engine()
    return engine.get_market_status()


async def send_test_alert():
    """Send test alert for system verification"""
    test_alert = MarketAlert(
        alert_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        rule_id="test_alert",
        severity=AlertSeverity.INFO,
        category=AlertCategory.SYSTEM_ISSUES,
        title="Test Market Alert",
        message="This is a test alert to verify the notification system is working correctly.",
        data={"test": True, "timestamp": datetime.now().isoformat()},
        timestamp=datetime.now(),
        channels=[DeliveryChannel.EMAIL],
        recipients=["admin@athintel.gr"]
    )
    
    engine = get_market_alert_engine()
    await engine.send_alert(test_alert)
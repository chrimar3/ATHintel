"""
Data Quality Monitoring System
Story 1.7: Monitor and alert on data quality issues
Production-ready quality assessment for property data
"""

import time
import json
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pathlib import Path
import statistics


@dataclass
class QualityMetric:
    """Individual quality metric"""
    name: str
    value: float
    threshold: float
    status: str  # 'good', 'warning', 'critical'
    message: str
    timestamp: datetime


@dataclass
class QualityScore:
    """Overall quality score for a dataset"""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    timeliness_score: float
    validity_score: float
    uniqueness_score: float
    total_properties: int
    timestamp: datetime
    metrics: List[QualityMetric]


@dataclass
class QualityAlert:
    """Quality alert"""
    alert_id: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    metric_name: str
    current_value: float
    threshold: float
    message: str
    timestamp: datetime
    acknowledged: bool = False


class DataQualityRules:
    """Data quality validation rules"""
    
    def __init__(self):
        self.rules = {
            # Completeness rules
            'required_fields': ['id', 'price', 'size', 'location'],
            'min_completeness_rate': 0.95,  # 95% of fields must be present
            
            # Accuracy rules
            'price_range': (10000, 5000000),    # €10K - €5M
            'size_range': (20, 1000),           # 20-1000 m²
            'rooms_range': (1, 10),             # 1-10 rooms
            
            # Consistency rules
            'price_per_m2_range': (500, 15000), # €500-15K per m²
            'room_size_ratio': (10, 200),       # 10-200 m² per room
            
            # Timeliness rules
            'max_age_days': 180,                # Data older than 6 months
            'freshness_rate_threshold': 0.8,    # 80% should be < 30 days old
            
            # Validity rules
            'valid_domains': ['spitogatos.gr', 'xe.gr', 'tospitimou.gr', 'plot.gr'],
            'min_url_validity': 0.9,            # 90% URLs should be valid
            
            # Uniqueness rules
            'max_duplicate_rate': 0.05,         # 5% duplicates allowed
        }
    
    def get_rule(self, rule_name: str, default=None):
        """Get rule value"""
        return self.rules.get(rule_name, default)


class DataQualityMonitor:
    """
    Production data quality monitoring system
    Continuously monitors and alerts on data quality issues
    """
    
    def __init__(self, db_path: str = "quality_monitoring.db"):
        self.db_path = db_path
        self.rules = DataQualityRules()
        self.logger = self._setup_logging()
        
        # Quality history (last 1000 scores)
        self.quality_history: deque = deque(maxlen=1000)
        
        # Active alerts
        self.active_alerts: List[QualityAlert] = []
        self.alert_lock = threading.Lock()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.last_check_time = None
        
        # Quality thresholds
        self.thresholds = {
            'overall_critical': 0.6,   # Below 60% = critical
            'overall_warning': 0.8,    # Below 80% = warning
            'metric_critical': 0.5,    # Individual metric critical
            'metric_warning': 0.7      # Individual metric warning
        }
        
        # Initialize database
        self._init_database()
        
        self.logger.info("Data Quality Monitor initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging"""
        logger = logging.getLogger('data_quality_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _init_database(self):
        """Initialize quality monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            # Quality scores table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    overall_score REAL,
                    completeness_score REAL,
                    accuracy_score REAL,
                    consistency_score REAL,
                    timeliness_score REAL,
                    validity_score REAL,
                    uniqueness_score REAL,
                    total_properties INTEGER,
                    timestamp TEXT
                )
            """)
            
            # Quality metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    score_id INTEGER,
                    name TEXT,
                    value REAL,
                    threshold REAL,
                    status TEXT,
                    message TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (score_id) REFERENCES quality_scores (id)
                )
            """)
            
            # Quality alerts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quality_alerts (
                    alert_id TEXT PRIMARY KEY,
                    severity TEXT,
                    metric_name TEXT,
                    current_value REAL,
                    threshold REAL,
                    message TEXT,
                    timestamp TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT
                )
            """)
    
    def assess_data_quality(self, properties: List[Dict[str, Any]]) -> QualityScore:
        """
        Assess overall data quality of property dataset
        
        Args:
            properties: List of property dictionaries
            
        Returns:
            QualityScore object
        """
        if not properties:
            return QualityScore(
                overall_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                timeliness_score=0.0,
                validity_score=0.0,
                uniqueness_score=0.0,
                total_properties=0,
                timestamp=datetime.now(),
                metrics=[]
            )
        
        self.logger.info(f"Assessing quality of {len(properties)} properties")
        
        # Calculate individual dimension scores
        completeness = self._assess_completeness(properties)
        accuracy = self._assess_accuracy(properties)
        consistency = self._assess_consistency(properties)
        timeliness = self._assess_timeliness(properties)
        validity = self._assess_validity(properties)
        uniqueness = self._assess_uniqueness(properties)
        
        # Calculate weighted overall score
        weights = {
            'completeness': 0.25,
            'accuracy': 0.25,
            'validity': 0.20,
            'consistency': 0.15,
            'timeliness': 0.10,
            'uniqueness': 0.05
        }
        
        overall_score = (
            completeness.value * weights['completeness'] +
            accuracy.value * weights['accuracy'] +
            validity.value * weights['validity'] +
            consistency.value * weights['consistency'] +
            timeliness.value * weights['timeliness'] +
            uniqueness.value * weights['uniqueness']
        )
        
        # Create quality score
        quality_score = QualityScore(
            overall_score=overall_score,
            completeness_score=completeness.value,
            accuracy_score=accuracy.value,
            consistency_score=consistency.value,
            timeliness_score=timeliness.value,
            validity_score=validity.value,
            uniqueness_score=uniqueness.value,
            total_properties=len(properties),
            timestamp=datetime.now(),
            metrics=[completeness, accuracy, consistency, timeliness, validity, uniqueness]
        )
        
        # Store in history
        self.quality_history.append(quality_score)
        
        # Save to database
        self._save_quality_score(quality_score)
        
        # Check for alerts
        self._check_quality_alerts(quality_score)
        
        self.logger.info(f"Quality assessment completed: {overall_score:.1%}")
        
        return quality_score
    
    def _assess_completeness(self, properties: List[Dict[str, Any]]) -> QualityMetric:
        """Assess data completeness"""
        required_fields = self.rules.get_rule('required_fields', [])
        
        if not required_fields:
            return QualityMetric(
                name="completeness",
                value=1.0,
                threshold=0.95,
                status="good",
                message="No required fields defined",
                timestamp=datetime.now()
            )
        
        total_expected = len(properties) * len(required_fields)
        total_present = 0
        
        for prop in properties:
            for field in required_fields:
                if field in prop and prop[field] is not None and str(prop[field]).strip():
                    total_present += 1
        
        completeness_rate = total_present / total_expected if total_expected > 0 else 0
        threshold = self.rules.get_rule('min_completeness_rate', 0.95)
        
        if completeness_rate >= threshold:
            status = "good"
            message = f"Completeness rate: {completeness_rate:.1%}"
        elif completeness_rate >= threshold * 0.8:
            status = "warning"
            message = f"Completeness rate below target: {completeness_rate:.1%}"
        else:
            status = "critical"
            message = f"Poor completeness rate: {completeness_rate:.1%}"
        
        return QualityMetric(
            name="completeness",
            value=completeness_rate,
            threshold=threshold,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
    
    def _assess_accuracy(self, properties: List[Dict[str, Any]]) -> QualityMetric:
        """Assess data accuracy"""
        accurate_count = 0
        total_count = len(properties)
        
        for prop in properties:
            is_accurate = True
            
            # Check price range
            price = prop.get('price', 0)
            if price > 0:
                price_range = self.rules.get_rule('price_range', (0, float('inf')))
                if not (price_range[0] <= price <= price_range[1]):
                    is_accurate = False
            
            # Check size range
            size = prop.get('size', 0)
            if size > 0:
                size_range = self.rules.get_rule('size_range', (0, float('inf')))
                if not (size_range[0] <= size <= size_range[1]):
                    is_accurate = False
            
            # Check rooms range
            rooms = prop.get('rooms', 0)
            if rooms > 0:
                rooms_range = self.rules.get_rule('rooms_range', (0, float('inf')))
                if not (rooms_range[0] <= rooms <= rooms_range[1]):
                    is_accurate = False
            
            if is_accurate:
                accurate_count += 1
        
        accuracy_rate = accurate_count / total_count if total_count > 0 else 0
        threshold = 0.9  # 90% accuracy threshold
        
        if accuracy_rate >= threshold:
            status = "good"
            message = f"Accuracy rate: {accuracy_rate:.1%}"
        elif accuracy_rate >= threshold * 0.8:
            status = "warning"
            message = f"Accuracy below target: {accuracy_rate:.1%}"
        else:
            status = "critical"
            message = f"Poor accuracy: {accuracy_rate:.1%}"
        
        return QualityMetric(
            name="accuracy",
            value=accuracy_rate,
            threshold=threshold,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
    
    def _assess_consistency(self, properties: List[Dict[str, Any]]) -> QualityMetric:
        """Assess data consistency"""
        consistent_count = 0
        total_checked = 0
        
        for prop in properties:
            price = prop.get('price', 0)
            size = prop.get('size', 0)
            rooms = prop.get('rooms', 0)
            
            if price > 0 and size > 0:
                total_checked += 1
                
                # Check price per m² consistency
                price_per_m2 = price / size
                price_range = self.rules.get_rule('price_per_m2_range', (0, float('inf')))
                
                price_consistent = price_range[0] <= price_per_m2 <= price_range[1]
                
                # Check room/size ratio consistency
                room_consistent = True
                if rooms > 0:
                    size_per_room = size / rooms
                    room_range = self.rules.get_rule('room_size_ratio', (0, float('inf')))
                    room_consistent = room_range[0] <= size_per_room <= room_range[1]
                
                if price_consistent and room_consistent:
                    consistent_count += 1
        
        consistency_rate = consistent_count / total_checked if total_checked > 0 else 1.0
        threshold = 0.85  # 85% consistency threshold
        
        if consistency_rate >= threshold:
            status = "good"
            message = f"Consistency rate: {consistency_rate:.1%}"
        elif consistency_rate >= threshold * 0.8:
            status = "warning"
            message = f"Consistency below target: {consistency_rate:.1%}"
        else:
            status = "critical"
            message = f"Poor consistency: {consistency_rate:.1%}"
        
        return QualityMetric(
            name="consistency",
            value=consistency_rate,
            threshold=threshold,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
    
    def _assess_timeliness(self, properties: List[Dict[str, Any]]) -> QualityMetric:
        """Assess data timeliness"""
        current_time = datetime.now()
        fresh_count = 0
        total_with_dates = 0
        
        for prop in properties:
            listed_date = prop.get('listed_date')
            if listed_date:
                total_with_dates += 1
                try:
                    if isinstance(listed_date, str):
                        # Parse ISO format date
                        prop_date = datetime.fromisoformat(listed_date.replace('Z', '+00:00').replace('+00:00', ''))
                    else:
                        prop_date = listed_date
                    
                    # Check if property is fresh (< 30 days old)
                    days_old = (current_time - prop_date).days
                    if days_old <= 30:
                        fresh_count += 1
                        
                except (ValueError, TypeError):
                    # Invalid date format
                    continue
        
        freshness_rate = fresh_count / total_with_dates if total_with_dates > 0 else 0
        threshold = self.rules.get_rule('freshness_rate_threshold', 0.8)
        
        if freshness_rate >= threshold:
            status = "good"
            message = f"Fresh data rate: {freshness_rate:.1%}"
        elif freshness_rate >= threshold * 0.7:
            status = "warning"
            message = f"Data freshness below target: {freshness_rate:.1%}"
        else:
            status = "critical"
            message = f"Stale data: {freshness_rate:.1%} fresh"
        
        return QualityMetric(
            name="timeliness",
            value=freshness_rate,
            threshold=threshold,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
    
    def _assess_validity(self, properties: List[Dict[str, Any]]) -> QualityMetric:
        """Assess data validity"""
        valid_count = 0
        total_count = len(properties)
        valid_domains = set(self.rules.get_rule('valid_domains', []))
        
        for prop in properties:
            is_valid = True
            
            # Check URL validity
            url = prop.get('url', '')
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    if valid_domains and domain not in valid_domains:
                        is_valid = False
                except:
                    is_valid = False
            
            # Check ID validity
            prop_id = prop.get('id')
            if not prop_id or not str(prop_id).strip():
                is_valid = False
            
            if is_valid:
                valid_count += 1
        
        validity_rate = valid_count / total_count if total_count > 0 else 0
        threshold = self.rules.get_rule('min_url_validity', 0.9)
        
        if validity_rate >= threshold:
            status = "good"
            message = f"Validity rate: {validity_rate:.1%}"
        elif validity_rate >= threshold * 0.8:
            status = "warning"
            message = f"Validity below target: {validity_rate:.1%}"
        else:
            status = "critical"
            message = f"Poor validity: {validity_rate:.1%}"
        
        return QualityMetric(
            name="validity",
            value=validity_rate,
            threshold=threshold,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
    
    def _assess_uniqueness(self, properties: List[Dict[str, Any]]) -> QualityMetric:
        """Assess data uniqueness"""
        seen_ids = set()
        duplicates = 0
        total_count = len(properties)
        
        for prop in properties:
            prop_id = prop.get('id')
            if prop_id:
                if prop_id in seen_ids:
                    duplicates += 1
                else:
                    seen_ids.add(prop_id)
        
        duplicate_rate = duplicates / total_count if total_count > 0 else 0
        uniqueness_rate = 1.0 - duplicate_rate
        threshold = 1.0 - self.rules.get_rule('max_duplicate_rate', 0.05)  # 95% unique
        
        if uniqueness_rate >= threshold:
            status = "good"
            message = f"Uniqueness rate: {uniqueness_rate:.1%}"
        elif uniqueness_rate >= threshold * 0.9:
            status = "warning"
            message = f"Some duplicates found: {duplicate_rate:.1%}"
        else:
            status = "critical"
            message = f"High duplicate rate: {duplicate_rate:.1%}"
        
        return QualityMetric(
            name="uniqueness",
            value=uniqueness_rate,
            threshold=threshold,
            status=status,
            message=message,
            timestamp=datetime.now()
        )
    
    def _save_quality_score(self, score: QualityScore):
        """Save quality score to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Insert score
            cursor = conn.execute("""
                INSERT INTO quality_scores 
                (overall_score, completeness_score, accuracy_score, consistency_score,
                 timeliness_score, validity_score, uniqueness_score, total_properties, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                score.overall_score,
                score.completeness_score,
                score.accuracy_score,
                score.consistency_score,
                score.timeliness_score,
                score.validity_score,
                score.uniqueness_score,
                score.total_properties,
                score.timestamp.isoformat()
            ))
            
            score_id = cursor.lastrowid
            
            # Insert metrics
            for metric in score.metrics:
                conn.execute("""
                    INSERT INTO quality_metrics
                    (score_id, name, value, threshold, status, message, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    score_id,
                    metric.name,
                    metric.value,
                    metric.threshold,
                    metric.status,
                    metric.message,
                    metric.timestamp.isoformat()
                ))
    
    def _check_quality_alerts(self, score: QualityScore):
        """Check for quality alerts"""
        new_alerts = []
        
        # Check overall score
        if score.overall_score < self.thresholds['overall_critical']:
            alert = self._create_alert(
                "overall_quality",
                "critical",
                score.overall_score,
                self.thresholds['overall_critical'],
                f"Overall quality critically low: {score.overall_score:.1%}"
            )
            new_alerts.append(alert)
        elif score.overall_score < self.thresholds['overall_warning']:
            alert = self._create_alert(
                "overall_quality",
                "high",
                score.overall_score,
                self.thresholds['overall_warning'],
                f"Overall quality below warning threshold: {score.overall_score:.1%}"
            )
            new_alerts.append(alert)
        
        # Check individual metrics
        for metric in score.metrics:
            if metric.status == "critical":
                alert = self._create_alert(
                    metric.name,
                    "high",
                    metric.value,
                    metric.threshold,
                    f"{metric.name.title()} quality critical: {metric.message}"
                )
                new_alerts.append(alert)
            elif metric.status == "warning":
                alert = self._create_alert(
                    metric.name,
                    "medium",
                    metric.value,
                    metric.threshold,
                    f"{metric.name.title()} quality warning: {metric.message}"
                )
                new_alerts.append(alert)
        
        # Add new alerts
        with self.alert_lock:
            for alert in new_alerts:
                # Check if similar alert already exists
                existing = any(
                    a.metric_name == alert.metric_name and a.severity == alert.severity
                    for a in self.active_alerts
                    if not a.acknowledged
                )
                
                if not existing:
                    self.active_alerts.append(alert)
                    self._save_alert(alert)
                    self.logger.warning(f"Quality Alert: {alert.message}")
    
    def _create_alert(self, metric_name: str, severity: str, current_value: float,
                     threshold: float, message: str) -> QualityAlert:
        """Create quality alert"""
        alert_id = f"{metric_name}_{severity}_{int(time.time())}"
        
        return QualityAlert(
            alert_id=alert_id,
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold,
            message=message,
            timestamp=datetime.now(),
            acknowledged=False
        )
    
    def _save_alert(self, alert: QualityAlert):
        """Save alert to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO quality_alerts
                (alert_id, severity, metric_name, current_value, threshold, 
                 message, timestamp, acknowledged)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id,
                alert.severity,
                alert.metric_name,
                alert.current_value,
                alert.threshold,
                alert.message,
                alert.timestamp.isoformat(),
                alert.acknowledged
            ))
    
    def get_quality_dashboard(self) -> Dict[str, Any]:
        """Get quality dashboard data"""
        latest_score = self.quality_history[-1] if self.quality_history else None
        
        # Get quality trend (last 24 hours)
        with sqlite3.connect(self.db_path) as conn:
            trend_data = conn.execute("""
                SELECT timestamp, overall_score, completeness_score, accuracy_score,
                       validity_score, total_properties
                FROM quality_scores
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 24
            """).fetchall()
        
        return {
            'current_quality': asdict(latest_score) if latest_score else None,
            'active_alerts': len([a for a in self.active_alerts if not a.acknowledged]),
            'total_alerts': len(self.active_alerts),
            'trend_24h': [
                {
                    'timestamp': row[0],
                    'overall_score': row[1],
                    'completeness_score': row[2],
                    'accuracy_score': row[3],
                    'validity_score': row[4],
                    'total_properties': row[5]
                }
                for row in trend_data
            ],
            'quality_history_count': len(self.quality_history),
            'monitoring_status': 'active' if self.is_monitoring else 'stopped'
        }
    
    def get_active_alerts(self) -> List[QualityAlert]:
        """Get active (unacknowledged) alerts"""
        with self.alert_lock:
            return [a for a in self.active_alerts if not a.acknowledged]
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        with self.alert_lock:
            for alert in self.active_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    
                    # Update database
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            UPDATE quality_alerts 
                            SET acknowledged = TRUE, resolved_at = ?
                            WHERE alert_id = ?
                        """, (datetime.now().isoformat(), alert_id))
                    
                    self.logger.info(f"Alert acknowledged: {alert_id}")
                    break


def create_quality_monitor(db_path: str = "quality_monitoring.db") -> DataQualityMonitor:
    """Factory function to create quality monitor"""
    return DataQualityMonitor(db_path)
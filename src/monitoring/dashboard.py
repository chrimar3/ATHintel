"""
Real-time Monitoring Dashboard
Story 1.3: Visual monitoring interface
Provides real-time and historical metrics visualization
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading

from .metrics_collector import get_metrics_collector


class MonitoringDashboard:
    """
    Real-time monitoring dashboard for validation metrics
    Provides both CLI and web-exportable views
    """
    
    def __init__(self, refresh_interval_seconds: int = 5):
        """
        Initialize monitoring dashboard
        
        Args:
            refresh_interval_seconds: Dashboard refresh interval
        """
        self.refresh_interval = refresh_interval_seconds
        self.collector = get_metrics_collector()
        self.running = False
        self.last_update = None
        
        # Dashboard components cache
        self.cache = {
            'real_time': {},
            'hourly': {},
            'daily': {},
            'factors': {},
            'alerts': []
        }
    
    def start(self) -> None:
        """Start dashboard monitoring"""
        self.running = True
        self._refresh_data()
        print("📊 Monitoring Dashboard Started")
        print(f"🔄 Refresh interval: {self.refresh_interval}s")
        print("-" * 80)
    
    def stop(self) -> None:
        """Stop dashboard monitoring"""
        self.running = False
        print("\n📊 Monitoring Dashboard Stopped")
    
    def display_cli(self) -> None:
        """Display dashboard in CLI format"""
        self._refresh_data()
        
        # Clear screen (works on Unix-like systems)
        print("\033[H\033[J", end="")
        
        # Header
        print("=" * 80)
        print("🎯 ATHintel Real-time Validation Monitor")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Real-time metrics
        self._display_real_time_section()
        
        # Hourly trends
        self._display_hourly_trends()
        
        # Factor analysis
        self._display_factor_analysis()
        
        # Active alerts
        self._display_alerts()
        
        # Footer
        print("=" * 80)
        print(f"Last updated: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'Never'}")
        print("Press Ctrl+C to exit")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data for web/API consumption
        
        Returns:
            Dashboard data dictionary
        """
        self._refresh_data()
        
        return {
            'timestamp': time.time(),
            'updated_at': datetime.now().isoformat(),
            'real_time': self.cache['real_time'],
            'hourly_trend': self.cache['hourly'],
            'daily_trend': self.cache['daily'],
            'factor_analysis': self.cache['factors'],
            'alerts': self.cache['alerts'],
            'config': {
                'refresh_interval': self.refresh_interval,
                'alert_thresholds': self.collector.alert_thresholds
            }
        }
    
    def export_report(self, output_path: str, format: str = 'html') -> None:
        """
        Export dashboard report
        
        Args:
            output_path: Output file path
            format: Export format ('html', 'json', 'markdown')
        """
        data = self.get_dashboard_data()
        output_path = Path(output_path)
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        elif format == 'html':
            html_content = self._generate_html_report(data)
            with open(output_path, 'w') as f:
                f.write(html_content)
        
        elif format == 'markdown':
            md_content = self._generate_markdown_report(data)
            with open(output_path, 'w') as f:
                f.write(md_content)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"✅ Report exported to {output_path}")
    
    def _refresh_data(self) -> None:
        """Refresh all dashboard data from collector"""
        self.cache['real_time'] = self.collector.get_real_time_metrics()
        self.cache['hourly'] = self.collector.get_historical_metrics(24)
        self.cache['daily'] = self.collector.get_historical_metrics(168)  # 7 days
        self.cache['factors'] = self.collector.get_factor_analysis()
        self.cache['alerts'] = self.collector.active_alerts
        self.last_update = datetime.now()
    
    def _display_real_time_section(self) -> None:
        """Display real-time metrics section"""
        rt = self.cache['real_time'].get('last_minute', {})
        
        print("\n📈 REAL-TIME METRICS (Last 60 seconds)")
        print("-" * 40)
        
        # Key metrics in columns
        print(f"{'Validations:':<20} {rt.get('total_validations', 0):>10,}")
        print(f"{'Valid:':<20} {rt.get('valid_count', 0):>10,} ({rt.get('validity_rate', 0):.1%})")
        print(f"{'Invalid:':<20} {rt.get('invalid_count', 0):>10,}")
        print(f"{'Avg Score:':<20} {rt.get('avg_score', 0):>10.1f}")
        print(f"{'Avg Time:':<20} {rt.get('avg_time_ms', 0):>10.2f} ms")
        print(f"{'Throughput:':<20} {rt.get('throughput_per_minute', 0):>10,}/min")
        
        # Visual throughput bar
        throughput = rt.get('throughput_per_minute', 0)
        bar_length = min(50, int(throughput / 100))
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"\nThroughput: [{bar}] {throughput:,}/min")
    
    def _display_hourly_trends(self) -> None:
        """Display hourly trend section"""
        hourly = self.cache['hourly']
        
        print("\n📊 24-HOUR TREND")
        print("-" * 40)
        
        if not hourly.get('data'):
            print("No data available")
            return
        
        # Get last 6 hours for mini chart
        recent_hours = hourly['data'][-6:] if len(hourly['data']) > 6 else hourly['data']
        
        # Mini sparkline chart
        max_val = max(h['total_validations'] for h in recent_hours) if recent_hours else 1
        
        for h in recent_hours:
            hour_label = datetime.fromtimestamp(h['timestamp']).strftime('%H:00')
            val = h['total_validations']
            bar_size = int((val / max_val) * 20) if max_val > 0 else 0
            bar = "▓" * bar_size + "░" * (20 - bar_size)
            print(f"{hour_label} [{bar}] {val:,} ({h['validity_rate']:.0%} valid)")
        
        # Summary stats
        if summary := hourly.get('summary'):
            print(f"\n24h Summary: {summary['total_validations']:,} total, "
                  f"{summary['overall_validity_rate']:.1%} valid, "
                  f"{summary['avg_score']:.1f} avg score")
    
    def _display_factor_analysis(self) -> None:
        """Display factor analysis section"""
        factors = self.cache['factors']
        
        print("\n🔍 FACTOR ANALYSIS (Last 1000 validations)")
        print("-" * 40)
        
        if not factors:
            print("No factor data available")
            return
        
        # Display each factor with performance bar
        for factor, stats in factors.items():
            avg_score = stats['avg_score']
            fail_rate = stats['failing_rate']
            
            # Performance indicator
            if avg_score >= 80:
                indicator = "🟢"
            elif avg_score >= 60:
                indicator = "🟡"
            else:
                indicator = "🔴"
            
            # Score bar
            bar_size = int(avg_score / 5)
            bar = "█" * bar_size + "░" * (20 - bar_size)
            
            print(f"{indicator} {factor:<15} [{bar}] {avg_score:.1f} (fail: {fail_rate:.1%})")
    
    def _display_alerts(self) -> None:
        """Display active alerts section"""
        alerts = self.cache['alerts']
        
        print("\n⚠️  ACTIVE ALERTS")
        print("-" * 40)
        
        if not alerts:
            print("✅ No active alerts")
            return
        
        for alert in alerts[-5:]:  # Show last 5 alerts
            time_ago = int(time.time() - alert['timestamp'])
            if time_ago < 60:
                time_str = f"{time_ago}s ago"
            else:
                time_str = f"{time_ago // 60}m ago"
            
            icon = "🔴" if 'error' in alert['type'] else "🟡"
            print(f"{icon} [{time_str}] {alert['message']}")
    
    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ATHintel Validation Monitor</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .metric-card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; 
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        .metric-label {{ color: #7f8c8d; margin-bottom: 5px; }}
        .alert {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px; 
                  border-left: 4px solid #ffc107; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .danger {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
        th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 ATHintel Validation Monitor</h1>
        <p>Generated: {data['updated_at']}</p>
    </div>
    
    <h2>📈 Real-time Metrics</h2>
    <div class="metric-card">
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
            <div>
                <div class="metric-label">Total Validations</div>
                <div class="metric-value">{data['real_time']['last_minute']['total_validations']:,}</div>
            </div>
            <div>
                <div class="metric-label">Validity Rate</div>
                <div class="metric-value">{data['real_time']['last_minute']['validity_rate']:.1%}</div>
            </div>
            <div>
                <div class="metric-label">Throughput</div>
                <div class="metric-value">{data['real_time']['last_minute']['throughput_per_minute']:,}/min</div>
            </div>
        </div>
    </div>
    
    <h2>📊 24-Hour Summary</h2>
    <div class="metric-card">
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Total Validations</td>
                <td>{data['hourly_trend'].get('summary', {}).get('total_validations', 0):,}</td>
            </tr>
            <tr>
                <td>Overall Validity Rate</td>
                <td>{data['hourly_trend'].get('summary', {}).get('overall_validity_rate', 0):.1%}</td>
            </tr>
            <tr>
                <td>Average Score</td>
                <td>{data['hourly_trend'].get('summary', {}).get('avg_score', 0):.1f}</td>
            </tr>
            <tr>
                <td>Average Response Time</td>
                <td>{data['hourly_trend'].get('summary', {}).get('avg_time_ms', 0):.2f} ms</td>
            </tr>
        </table>
    </div>
    
    <h2>⚠️ Active Alerts</h2>
    <div class="metric-card">
        {''.join(f'<div class="alert">{alert["message"]}</div>' for alert in data.get('alerts', []))}
        {'' if data.get('alerts') else '<p class="success">✅ No active alerts</p>'}
    </div>
</body>
</html>"""
        return html
    
    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report"""
        md = f"""# ATHintel Validation Monitor Report

**Generated**: {data['updated_at']}

## 📈 Real-time Metrics (Last 60 seconds)

| Metric | Value |
|--------|-------|
| Total Validations | {data['real_time']['last_minute']['total_validations']:,} |
| Valid | {data['real_time']['last_minute']['valid_count']:,} |
| Invalid | {data['real_time']['last_minute']['invalid_count']:,} |
| Validity Rate | {data['real_time']['last_minute']['validity_rate']:.1%} |
| Average Score | {data['real_time']['last_minute']['avg_score']:.1f} |
| Average Time | {data['real_time']['last_minute']['avg_time_ms']:.2f} ms |
| Throughput | {data['real_time']['last_minute']['throughput_per_minute']:,}/min |

## 📊 24-Hour Summary

"""
        
        if summary := data['hourly_trend'].get('summary'):
            md += f"""
- **Total Validations**: {summary['total_validations']:,}
- **Overall Validity Rate**: {summary['overall_validity_rate']:.1%}
- **Average Score**: {summary['avg_score']:.1f}
- **Average Response Time**: {summary['avg_time_ms']:.2f} ms
- **Average Throughput**: {summary['avg_throughput_per_hour']:.0f}/hour

"""
        
        md += "## ⚠️ Active Alerts\n\n"
        if data.get('alerts'):
            for alert in data['alerts']:
                md += f"- **{alert['type']}**: {alert['message']}\n"
        else:
            md += "✅ No active alerts\n"
        
        return md


def run_dashboard_cli(duration_seconds: int = 0):
    """
    Run dashboard in CLI mode
    
    Args:
        duration_seconds: Duration to run (0 for infinite)
    """
    dashboard = MonitoringDashboard(refresh_interval_seconds=5)
    dashboard.start()
    
    start_time = time.time()
    try:
        while True:
            dashboard.display_cli()
            time.sleep(dashboard.refresh_interval)
            
            if duration_seconds > 0 and time.time() - start_time > duration_seconds:
                break
                
    except KeyboardInterrupt:
        print("\n\nStopping dashboard...")
    finally:
        dashboard.stop()


if __name__ == "__main__":
    # Run CLI dashboard
    run_dashboard_cli()
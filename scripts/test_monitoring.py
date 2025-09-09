#!/usr/bin/env python3
"""
Test Monitoring Dashboard
Story 1.3: Demonstrate real-time monitoring capabilities
"""

import sys
import time
import json
import random
import threading
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validators.property_validator import PropertyValidator
from monitoring.dashboard import MonitoringDashboard
from config.feature_flags import FeatureFlags


def generate_test_property(idx: int) -> dict:
    """Generate test property data"""
    locations = ['Kolonaki', 'Glyfada', 'Kifisia', 'Exarchia', 'Piraeus']
    
    # Mix of valid and invalid properties
    if random.random() > 0.2:  # 80% valid
        return {
            'id': f'test_{idx:04d}',
            'url': f'https://spitogatos.gr/property/{random.randint(10000, 99999)}',
            'price': random.randint(150000, 800000),
            'size': random.randint(50, 200),
            'rooms': random.randint(1, 5),
            'floor': random.randint(0, 8),
            'location': random.choice(locations),
            'listed_date': datetime.now().isoformat(),
            'images': [f'img{i}.jpg' for i in range(random.randint(3, 10))],
            'year_built': random.randint(1980, 2023)
        }
    else:  # 20% invalid
        return {
            'id': f'invalid_{idx:04d}',
            'url': 'https://fake-site.com/property/123' if random.random() > 0.5 else '',
            'price': -100000 if random.random() > 0.5 else 15000000,
            'size': 10 if random.random() > 0.5 else 600,
            'rooms': 15 if random.random() > 0.5 else 0,
            'location': 'Unknown' if random.random() > 0.5 else '',
            'listed_date': '2030-01-01' if random.random() > 0.5 else 'invalid-date'
        }


def validation_worker(validator: PropertyValidator, num_properties: int, delay_ms: float):
    """Worker thread to perform validations"""
    print(f"🔄 Starting validation worker: {num_properties} properties, {delay_ms}ms delay")
    
    for i in range(num_properties):
        property_data = generate_test_property(i)
        validator.validate_property(property_data)
        
        # Variable delay to simulate real-world load
        if delay_ms > 0:
            time.sleep(delay_ms / 1000 + random.random() * 0.01)


def main():
    """Run monitoring dashboard test"""
    print("=" * 80)
    print("🎯 ATHintel Monitoring Dashboard Test")
    print("=" * 80)
    
    # Enable feature flags for monitoring
    ff = FeatureFlags()
    ff.enable("monitoring_enabled")
    ff.enable("multi_factor_validation")
    ff.enable("validation_logging")
    print("✅ Feature flags enabled")
    
    # Initialize validator
    validator = PropertyValidator()
    print("✅ Validator initialized")
    
    # Initialize dashboard
    dashboard = MonitoringDashboard(refresh_interval_seconds=2)
    print("✅ Dashboard initialized")
    
    # Start validation in background thread
    print("\n📊 Starting validation simulation...")
    print("- Generating mix of valid (80%) and invalid (20%) properties")
    print("- Simulating variable load patterns")
    print("-" * 40)
    
    # Create multiple worker threads for realistic load
    workers = []
    
    # Wave 1: Initial burst
    print("\n🌊 Wave 1: Initial burst (1000 properties)")
    worker1 = threading.Thread(
        target=validation_worker,
        args=(validator, 1000, 5)  # 5ms delay = ~200/sec
    )
    worker1.start()
    workers.append(worker1)
    
    # Let dashboard show initial data
    time.sleep(5)
    
    # Display dashboard snapshot
    dashboard_data = dashboard.get_dashboard_data()
    print("\n📈 Real-time Metrics:")
    print(f"  Validations: {dashboard_data['real_time']['last_minute']['total_validations']}")
    print(f"  Validity Rate: {dashboard_data['real_time']['last_minute']['validity_rate']:.1%}")
    print(f"  Throughput: {dashboard_data['real_time']['last_minute']['throughput_per_minute']}/min")
    
    # Wave 2: Sustained load
    print("\n🌊 Wave 2: Sustained load (2000 properties)")
    worker2 = threading.Thread(
        target=validation_worker,
        args=(validator, 2000, 10)  # 10ms delay = ~100/sec
    )
    worker2.start()
    workers.append(worker2)
    
    # Monitor for 10 seconds
    print("\n⏱️ Monitoring for 10 seconds...")
    for i in range(5):
        time.sleep(2)
        metrics = dashboard.get_dashboard_data()['real_time']['last_minute']
        print(f"  [{i*2+2}s] Throughput: {metrics['throughput_per_minute']:,}/min, "
              f"Valid: {metrics['validity_rate']:.1%}")
    
    # Wave 3: Spike test
    print("\n🌊 Wave 3: Spike test (5000 properties, no delay)")
    worker3 = threading.Thread(
        target=validation_worker,
        args=(validator, 5000, 0)  # No delay = max throughput
    )
    worker3.start()
    workers.append(worker3)
    
    # Wait for workers to complete
    print("\n⏳ Waiting for validation to complete...")
    for worker in workers:
        worker.join(timeout=30)
    
    # Final metrics
    print("\n" + "=" * 80)
    print("📊 FINAL METRICS")
    print("=" * 80)
    
    final_data = dashboard.get_dashboard_data()
    
    # Real-time summary
    rt = final_data['real_time']['last_minute']
    print(f"\n📈 Last Minute Performance:")
    print(f"  Total Validations: {rt['total_validations']:,}")
    print(f"  Valid: {rt['valid_count']:,} ({rt['validity_rate']:.1%})")
    print(f"  Invalid: {rt['invalid_count']:,}")
    print(f"  Average Score: {rt['avg_score']:.1f}")
    print(f"  Average Time: {rt['avg_time_ms']:.2f}ms")
    print(f"  Peak Throughput: {rt['throughput_per_minute']:,}/min")
    
    # Factor analysis
    factors = dashboard.collector.get_factor_analysis()
    if factors:
        print(f"\n🔍 Factor Analysis:")
        for factor, stats in factors.items():
            status = "🟢" if stats['avg_score'] >= 80 else "🟡" if stats['avg_score'] >= 60 else "🔴"
            print(f"  {status} {factor}: {stats['avg_score']:.1f} (fail rate: {stats['failing_rate']:.1%})")
    
    # Active alerts
    if final_data['alerts']:
        print(f"\n⚠️ Active Alerts:")
        for alert in final_data['alerts'][-5:]:
            print(f"  - {alert['type']}: {alert['message']}")
    else:
        print(f"\n✅ No active alerts")
    
    # Export reports
    print("\n📁 Exporting Reports...")
    
    # HTML report
    dashboard.export_report('monitoring_report.html', format='html')
    print("  ✅ HTML report: monitoring_report.html")
    
    # JSON data
    dashboard.export_report('monitoring_data.json', format='json')
    print("  ✅ JSON data: monitoring_data.json")
    
    # Markdown report
    dashboard.export_report('monitoring_report.md', format='markdown')
    print("  ✅ Markdown report: monitoring_report.md")
    
    # Validator statistics
    stats = validator.get_statistics()
    print(f"\n📊 Validator Statistics:")
    print(f"  Total Validated: {stats['total_validated']:,}")
    print(f"  Throughput: {stats['properties_per_minute']:,.0f} properties/minute")
    print(f"  Uptime: {stats['uptime']:.1f} seconds")
    
    print("\n✅ Monitoring test completed successfully!")


if __name__ == "__main__":
    main()
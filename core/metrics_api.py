"""
Performance metrics API for AuroraFIM.
Provides easy access to performance data for dashboards and reports.
"""

import sys
import os

# Ensure proper imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.performance_monitor import performance_monitor


def get_performance_report() -> dict:
    """Get a comprehensive performance report."""
    return performance_monitor.get_performance_summary()


def get_pool_status() -> dict:
    """Get database pool health status."""
    return performance_monitor.get_pool_health()


def get_logging_status() -> dict:
    """Get logging system health status."""
    return performance_monitor.get_logging_health()


def get_alerts() -> list:
    """Get all active alerts from the last hour."""
    return performance_monitor.get_active_alerts()


def export_metrics() -> str:
    """Export all metrics as JSON."""
    return performance_monitor.export_metrics_json()


def print_performance_report():
    """Print a formatted performance report to console."""
    report = performance_monitor.get_performance_summary()
    
    print("\n" + "="*70)
    print("AURORAFIM PERFORMANCE REPORT")
    print("="*70)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Uptime: {report['uptime']}")
    
    print("\n[DATABASE POOL]")
    for key, value in report['database_pool'].items():
        print(f"  {key:.<40} {value}")
    
    print("\n[LOGGING]")
    for key, value in report['logging'].items():
        if key != 'by_level':
            print(f"  {key:.<40} {value}")
    
    print("\n  By Level:")
    for level, count in report['logging']['by_level'].items():
        print(f"    {level:.<35} {count}")
    
    print("\n[ALERTS]")
    if report['alerts']['active_count'] > 0:
        for alert in report['alerts']['recent_alerts']:
            print(f"  [{alert['type']}] {alert['message']}")
            print(f"    at {alert['timestamp']}")
    else:
        print("  No active alerts")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    print_performance_report()

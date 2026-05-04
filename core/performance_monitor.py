"""
Performance monitoring for AuroraFIM database pool and logging.
Tracks metrics for connection pooling, logging, and application performance.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import json


class PerformanceMonitor:
    """Singleton performance monitor for tracking application metrics."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.lock = threading.Lock()
        self.start_time = datetime.now()
        
        # Database pool metrics
        self.pool_metrics = {
            'total_connections_created': 0,
            'total_connections_released': 0,
            'peak_utilization': 0,
            'connection_errors': 0,
            'average_wait_time': 0.0,
            'wait_times': [],  # List of wait times for averaging
        }
        
        # Logging metrics
        self.log_metrics = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0,
        }
        
        # Time-series data (last 60 minutes)
        self.log_timeseries = defaultdict(int)  # timestamp -> count
        self.pool_utilization_series = []  # List of (timestamp, utilization) tuples
        
        # Alert thresholds
        self.alert_thresholds = {
            'connection_pool_utilization': 0.9,  # Alert at 90% utilization
            'average_wait_time': 5.0,  # Alert if avg wait > 5 seconds
            'error_rate': 0.05,  # Alert if error rate > 5%
        }
        
        # Active alerts
        self.active_alerts = []
    
    # ==================== Database Pool Metrics ====================
    
    def record_connection_acquired(self, wait_time: float = 0.0):
        """Record a connection acquired from pool."""
        with self.lock:
            self.pool_metrics['total_connections_created'] += 1
            if wait_time > 0:
                self.pool_metrics['wait_times'].append(wait_time)
                # Keep only last 100 wait times for average calculation
                if len(self.pool_metrics['wait_times']) > 100:
                    self.pool_metrics['wait_times'].pop(0)
                self._update_average_wait_time()
    
    def record_connection_released(self):
        """Record a connection returned to pool."""
        with self.lock:
            self.pool_metrics['total_connections_released'] += 1
    
    def record_connection_error(self):
        """Record a connection pool error."""
        with self.lock:
            self.pool_metrics['connection_errors'] += 1
            self._check_error_threshold()
    
    def update_pool_utilization(self, active_connections: int, pool_size: int):
        """Update current pool utilization percentage."""
        with self.lock:
            utilization = active_connections / pool_size if pool_size > 0 else 0
            if utilization > self.pool_metrics['peak_utilization']:
                self.pool_metrics['peak_utilization'] = utilization
            
            # Record time-series data
            self.pool_utilization_series.append((datetime.now(), utilization))
            # Keep only last 60 minutes
            cutoff_time = datetime.now() - timedelta(minutes=60)
            self.pool_utilization_series = [
                (ts, util) for ts, util in self.pool_utilization_series
                if ts > cutoff_time
            ]
            
            # Check threshold
            if utilization > self.alert_thresholds['connection_pool_utilization']:
                self._add_alert(
                    'HIGH_POOL_UTILIZATION',
                    f'Connection pool utilization at {utilization*100:.1f}%'
                )
    
    def _update_average_wait_time(self):
        """Update average connection wait time."""
        if self.pool_metrics['wait_times']:
            avg = sum(self.pool_metrics['wait_times']) / len(self.pool_metrics['wait_times'])
            self.pool_metrics['average_wait_time'] = avg
            
            if avg > self.alert_thresholds['average_wait_time']:
                self._add_alert(
                    'HIGH_WAIT_TIME',
                    f'Average connection wait time: {avg:.2f}s'
                )
    
    # ==================== Logging Metrics ====================
    
    def record_log_message(self, level: str):
        """Record a log message by level."""
        with self.lock:
            if level in self.log_metrics:
                self.log_metrics[level] += 1
                
                # Record time-series (hourly buckets)
                hour_key = datetime.now().strftime('%Y-%m-%d %H:00:00')
                self.log_timeseries[hour_key] += 1
    
    def get_log_level_distribution(self) -> Dict[str, int]:
        """Get count of messages by log level."""
        with self.lock:
            return dict(self.log_metrics)
    
    def get_total_log_messages(self) -> int:
        """Get total number of log messages."""
        with self.lock:
            return sum(self.log_metrics.values())
    
    def get_error_rate(self) -> float:
        """Get percentage of ERROR and CRITICAL messages."""
        with self.lock:
            total = sum(self.log_metrics.values())
            if total == 0:
                return 0.0
            errors = self.log_metrics['ERROR'] + self.log_metrics['CRITICAL']
            return errors / total
    
    def _check_error_threshold(self):
        """Check if error rate exceeds threshold."""
        error_rate = self.get_error_rate()
        if error_rate > self.alert_thresholds['error_rate']:
            self._add_alert(
                'HIGH_ERROR_RATE',
                f'Error rate: {error_rate*100:.1f}%'
            )
    
    # ==================== Alert Management ====================
    
    def _add_alert(self, alert_type: str, message: str):
        """Add an alert if not already present."""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Avoid duplicate alerts within 5 minutes
        five_min_ago = datetime.now() - timedelta(minutes=5)
        recent_same_alerts = [
            a for a in self.active_alerts
            if a['type'] == alert_type and
            datetime.fromisoformat(a['timestamp']) > five_min_ago
        ]
        
        if not recent_same_alerts:
            self.active_alerts.append(alert)
            # Keep only last 100 alerts
            if len(self.active_alerts) > 100:
                self.active_alerts.pop(0)
    
    def get_active_alerts(self) -> List[Dict]:
        """Get all active alerts from the last hour."""
        with self.lock:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            return [
                a for a in self.active_alerts
                if datetime.fromisoformat(a['timestamp']) > one_hour_ago
            ]
    
    def clear_alerts(self):
        """Clear all alerts."""
        with self.lock:
            self.active_alerts.clear()
    
    # ==================== Reports ====================
    
    def get_uptime(self) -> str:
        """Get application uptime."""
        delta = datetime.now() - self.start_time
        days, remainder = divmod(int(delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary."""
        with self.lock:
            total_logs = sum(self.log_metrics.values())
            
            return {
                'timestamp': datetime.now().isoformat(),
                'uptime': self.get_uptime(),
                'database_pool': {
                    'total_connections_created': self.pool_metrics['total_connections_created'],
                    'total_connections_released': self.pool_metrics['total_connections_released'],
                    'active_connections': (
                        self.pool_metrics['total_connections_created'] -
                        self.pool_metrics['total_connections_released']
                    ),
                    'peak_utilization': f"{self.pool_metrics['peak_utilization']*100:.1f}%",
                    'average_wait_time': f"{self.pool_metrics['average_wait_time']:.2f}s",
                    'connection_errors': self.pool_metrics['connection_errors'],
                    'error_rate': f"{(self.pool_metrics['connection_errors'] / max(self.pool_metrics['total_connections_created'], 1) * 100):.2f}%",
                },
                'logging': {
                    'total_messages': total_logs,
                    'by_level': dict(self.log_metrics),
                    'error_rate': f"{self.get_error_rate()*100:.1f}%",
                    'info_percentage': f"{(self.log_metrics['INFO']/max(total_logs, 1)*100):.1f}%",
                    'warning_percentage': f"{(self.log_metrics['WARNING']/max(total_logs, 1)*100):.1f}%",
                    'error_percentage': f"{((self.log_metrics['ERROR']+self.log_metrics['CRITICAL'])/max(total_logs, 1)*100):.1f}%",
                },
                'alerts': {
                    'active_count': len(self.get_active_alerts()),
                    'recent_alerts': self.get_active_alerts()[-5:],  # Last 5 alerts
                },
            }
    
    def get_pool_health(self) -> Dict:
        """Get database pool health status."""
        summary = self.get_performance_summary()
        error_rate = self.pool_metrics['connection_errors'] / max(
            self.pool_metrics['total_connections_created'], 1
        )
        
        if error_rate > self.alert_thresholds['error_rate']:
            status = 'CRITICAL'
        elif self.pool_metrics['peak_utilization'] > 0.8:
            status = 'WARNING'
        else:
            status = 'HEALTHY'
        
        return {
            'status': status,
            'metrics': summary['database_pool'],
            'alerts': [a for a in self.active_alerts if 'POOL' in a['type'] or 'WAIT' in a['type']],
        }
    
    def get_logging_health(self) -> Dict:
        """Get logging health status."""
        summary = self.get_performance_summary()
        error_rate = self.get_error_rate()
        
        if error_rate > 0.1:
            status = 'CRITICAL'
        elif error_rate > 0.05:
            status = 'WARNING'
        else:
            status = 'HEALTHY'
        
        return {
            'status': status,
            'metrics': summary['logging'],
            'alerts': [a for a in self.active_alerts if 'ERROR' in a['type']],
        }
    
    def export_metrics_json(self) -> str:
        """Export all metrics as JSON string."""
        with self.lock:
            data = {
                'timestamp': datetime.now().isoformat(),
                'summary': self.get_performance_summary(),
                'pool_health': self.get_pool_health(),
                'logging_health': self.get_logging_health(),
            }
            return json.dumps(data, indent=2, default=str)
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        with self.lock:
            self.pool_metrics = {
                'total_connections_created': 0,
                'total_connections_released': 0,
                'peak_utilization': 0,
                'connection_errors': 0,
                'average_wait_time': 0.0,
                'wait_times': [],
            }
            self.log_metrics = {
                'DEBUG': 0,
                'INFO': 0,
                'WARNING': 0,
                'ERROR': 0,
                'CRITICAL': 0,
            }
            self.log_timeseries.clear()
            self.pool_utilization_series.clear()
            self.active_alerts.clear()


# Global singleton instance
performance_monitor = PerformanceMonitor()

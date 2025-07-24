import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import deque
import threading

class LoggingService:
    """
    Centralized logging service for the PoseWeaver application.
    Provides structured logging with different levels and components.
    """
    
    def __init__(self, max_logs=1000):
        self.max_logs = max_logs
        self.logs = deque(maxlen=max_logs)
        self.lock = threading.Lock()
        
        # Setup logging configuration
        self.setup_logging()
        
        # Get logger instance
        self.logger = logging.getLogger('poseweaver')
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(logs_dir, 'app.log')),
                logging.StreamHandler()
            ]
        )
        
    def log(self, level: str, component: str, message: str, extra_data: Optional[Dict] = None):
        """
        Log a message with structured data
        
        Args:
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            component: Component/module name (e.g., 'Auth', 'Database', 'API')
            message: Log message
            extra_data: Additional data to include in log
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'level': level.upper(),
            'component': component,
            'message': message,
            'extra_data': extra_data or {}
        }
        
        # Add to in-memory logs
        with self.lock:
            self.logs.append(log_entry)
        
        # Log to file/console using standard logging
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{component}] {message}", extra=extra_data or {})
        
    def info(self, component: str, message: str, extra_data: Optional[Dict] = None):
        """Log info message"""
        self.log('INFO', component, message, extra_data)
        
    def warning(self, component: str, message: str, extra_data: Optional[Dict] = None):
        """Log warning message"""
        self.log('WARNING', component, message, extra_data)
        
    def error(self, component: str, message: str, extra_data: Optional[Dict] = None):
        """Log error message"""
        self.log('ERROR', component, message, extra_data)
        
    def debug(self, component: str, message: str, extra_data: Optional[Dict] = None):
        """Log debug message"""
        self.log('DEBUG', component, message, extra_data)
        
    def get_recent_logs(self, limit: int = 50, level_filter: Optional[str] = None, 
                       component_filter: Optional[str] = None) -> List[Dict]:
        """
        Get recent logs with optional filtering
        
        Args:
            limit: Maximum number of logs to return
            level_filter: Filter by log level (INFO, WARNING, ERROR, DEBUG)
            component_filter: Filter by component name
            
        Returns:
            List of log entries
        """
        with self.lock:
            logs = list(self.logs)
            
        # Apply filters
        if level_filter:
            logs = [log for log in logs if log['level'] == level_filter.upper()]
            
        if component_filter:
            logs = [log for log in logs if log['component'].lower() == component_filter.lower()]
            
        # Sort by timestamp (most recent first) and limit
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return logs[:limit]
        
    def get_logs_by_timeframe(self, hours: int = 24) -> List[Dict]:
        """
        Get logs from the last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of log entries from the specified timeframe
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            logs = list(self.logs)
            
        # Filter by timestamp
        filtered_logs = []
        for log in logs:
            try:
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time >= cutoff_time:
                    filtered_logs.append(log)
            except (ValueError, KeyError):
                continue
                
        # Sort by timestamp (most recent first)
        filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return filtered_logs
        
    def get_log_stats(self) -> Dict:
        """
        Get statistics about logs
        
        Returns:
            Dictionary with log statistics
        """
        with self.lock:
            logs = list(self.logs)
            
        if not logs:
            return {
                'total_logs': 0,
                'by_level': {},
                'by_component': {},
                'recent_errors': 0
            }
            
        # Count by level
        level_counts = {}
        component_counts = {}
        recent_errors = 0
        
        # Get cutoff for recent errors (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        
        for log in logs:
            # Count by level
            level = log.get('level', 'UNKNOWN')
            level_counts[level] = level_counts.get(level, 0) + 1
            
            # Count by component
            component = log.get('component', 'UNKNOWN')
            component_counts[component] = component_counts.get(component, 0) + 1
            
            # Count recent errors
            try:
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time >= recent_cutoff and level == 'ERROR':
                    recent_errors += 1
            except (ValueError, KeyError):
                continue
                
        return {
            'total_logs': len(logs),
            'by_level': level_counts,
            'by_component': component_counts,
            'recent_errors': recent_errors
        }
        
    def clear_logs(self):
        """Clear all in-memory logs"""
        with self.lock:
            self.logs.clear()
            
    def export_logs(self, filename: Optional[str] = None) -> str:
        """
        Export logs to JSON file
        
        Args:
            filename: Optional filename, defaults to timestamp-based name
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'poseweaver_logs_{timestamp}.json'
            
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        filepath = os.path.join(logs_dir, filename)
        
        with self.lock:
            logs = list(self.logs)
            
        with open(filepath, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
            
        return filepath

# Global logging service instance
_logging_service = None

def get_logging_service() -> LoggingService:
    """Get the global logging service instance"""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service

# Convenience functions for easy logging
def log_info(component: str, message: str, extra_data: Optional[Dict] = None):
    """Log info message"""
    get_logging_service().info(component, message, extra_data)

def log_warning(component: str, message: str, extra_data: Optional[Dict] = None):
    """Log warning message"""
    get_logging_service().warning(component, message, extra_data)

def log_error(component: str, message: str, extra_data: Optional[Dict] = None):
    """Log error message"""
    get_logging_service().error(component, message, extra_data)

def log_debug(component: str, message: str, extra_data: Optional[Dict] = None):
    """Log debug message"""
    get_logging_service().debug(component, message, extra_data)

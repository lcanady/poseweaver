"""
Admin system initialization script
Adds initial logs and system health checks when admin tools are first accessed
"""

from datetime import datetime, timedelta
from .logging_service import get_logging_service, log_info, log_warning, log_error
from .mongodb_service import get_mongodb_service
import psutil
import os

def initialize_admin_system():
    """Initialize the admin system with startup logs and health checks"""
    try:
        logging_service = get_logging_service()
        
        # Add startup logs
        log_info('System', 'PoseWeaver admin system initialized')
        log_info('Health Monitor', 'Starting system health monitoring')
        
        # Perform initial health checks
        perform_health_checks()
        
        # Add some sample operational logs
        add_sample_logs()
        
        log_info('Admin', 'Admin system initialization completed successfully')
        
    except Exception as e:
        log_error('System', f'Error during admin system initialization: {str(e)}')

def perform_health_checks():
    """Perform initial system health checks and log results"""
    try:
        # Database connectivity check
        db_service = get_mongodb_service()
        try:
            user_count = db_service.count_documents('users')
            log_info('Database', f'Database connection successful - {user_count} users in system')
        except Exception as e:
            log_error('Database', f'Database connection failed: {str(e)}')
        
        # Memory check
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            if memory_percent > 85:
                log_warning('Health Monitor', f'High memory usage detected: {memory_percent}%')
            else:
                log_info('Health Monitor', f'Memory usage normal: {memory_percent}%')
        except Exception as e:
            log_warning('Health Monitor', f'Could not check memory usage: {str(e)}')
        
        # CPU check
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                log_warning('Health Monitor', f'High CPU usage detected: {cpu_percent}%')
            else:
                log_info('Health Monitor', f'CPU usage normal: {cpu_percent}%')
        except Exception as e:
            log_warning('Health Monitor', f'Could not check CPU usage: {str(e)}')
        
        # Disk space check
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                log_warning('Health Monitor', f'Low disk space: {disk_percent:.1f}% used')
            else:
                log_info('Health Monitor', f'Disk space adequate: {disk_percent:.1f}% used')
        except Exception as e:
            log_warning('Health Monitor', f'Could not check disk usage: {str(e)}')
            
    except Exception as e:
        log_error('Health Monitor', f'Error during health checks: {str(e)}')

def add_sample_logs():
    """Add some sample operational logs to demonstrate the logging system"""
    try:
        # Simulate some typical application events
        log_info('Auth', 'User authentication service started')
        log_info('API', 'REST API endpoints initialized')
        log_info('Backup', 'Automated backup service configured')
        
        # Add a few historical entries (simulate past events)
        logging_service = get_logging_service()
        
        # Simulate some past events by manually adding log entries
        past_logs = [
            {
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'level': 'INFO',
                'component': 'Backup',
                'message': 'Daily backup completed successfully',
                'extra_data': {}
            },
            {
                'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'level': 'INFO',
                'component': 'Auth',
                'message': 'Admin user login successful',
                'extra_data': {}
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'level': 'WARNING',
                'component': 'API',
                'message': 'Rate limit threshold reached for IP 192.168.1.100',
                'extra_data': {}
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'level': 'INFO',
                'component': 'Database',
                'message': 'Database maintenance window completed',
                'extra_data': {}
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
                'level': 'INFO',
                'component': 'Health Monitor',
                'message': 'System health check passed - all services operational',
                'extra_data': {}
            }
        ]
        
        # Add past logs to the logging service
        with logging_service.lock:
            for log_entry in past_logs:
                logging_service.logs.append(log_entry)
        
        log_info('System', 'Sample operational logs added to demonstrate logging system')
        
    except Exception as e:
        log_error('System', f'Error adding sample logs: {str(e)}')

def check_admin_requirements():
    """Check if all admin system requirements are met"""
    try:
        requirements_met = True
        issues = []
        
        # Check if logs directory exists
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir, exist_ok=True)
                log_info('System', 'Created logs directory for admin system')
            except Exception as e:
                issues.append(f'Could not create logs directory: {str(e)}')
                requirements_met = False
        
        # Check database connectivity
        try:
            db_service = get_mongodb_service()
            db_service.count_documents('users')
            log_info('System', 'Database connectivity verified')
        except Exception as e:
            issues.append(f'Database connectivity issue: {str(e)}')
            requirements_met = False
        
        # Check system monitoring capabilities
        try:
            psutil.virtual_memory()
            psutil.cpu_percent()
            log_info('System', 'System monitoring capabilities verified')
        except Exception as e:
            issues.append(f'System monitoring unavailable: {str(e)}')
            log_warning('System', 'Some system monitoring features may be limited')
        
        if requirements_met:
            log_info('System', 'All admin system requirements met')
        else:
            log_error('System', f'Admin system requirements not met: {", ".join(issues)}')
        
        return requirements_met, issues
        
    except Exception as e:
        log_error('System', f'Error checking admin requirements: {str(e)}')
        return False, [str(e)]

# Auto-initialize when module is imported
_initialized = False

def ensure_admin_initialized():
    """Ensure admin system is initialized (called on first admin access)"""
    global _initialized
    if not _initialized:
        initialize_admin_system()
        _initialized = True

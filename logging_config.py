"""
Production Error Handling & Logging System
Enterprise-grade logging with structured output and error tracking
"""

import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


class Logger:
    """Production logger with structured output"""
    
    def __init__(self, name: str = "oraclai"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler (structured JSON)
        log_dir = os.environ.get('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            f'{log_dir}/app.json',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredLogFormatter())
        self.logger.addHandler(file_handler)
        
        # Error file handler (separate file for errors)
        error_handler = RotatingFileHandler(
            f'{log_dir}/errors.json',
            maxBytes=10*1024*1024,
            backupCount=10
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredLogFormatter())
        self.logger.addHandler(error_handler)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with extra fields"""
        extra = {}
        for key in ['user_id', 'request_id', 'endpoint', 'duration_ms', 'data']:
            if key in kwargs:
                extra[key] = kwargs[key]
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        self._log(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        self._log(logging.CRITICAL, message, exc_info=exc_info, **kwargs)


# Global logger instance
log = Logger()


class AppError(Exception):
    """Base application error with structured information"""
    
    def __init__(self, message: str, code: str = "UNKNOWN", 
                 status_code: int = 500, details: Optional[Dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.traceback = traceback.format_exc() if sys.exc_info()[0] else None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "status_code": self.status_code,
                "details": self.details,
                "timestamp": self.timestamp
            }
        }


class ValidationError(AppError):
    """Input validation error"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class AuthenticationError(AppError):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class AuthorizationError(AppError):
    """Authorization failed - insufficient permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)


class NotFoundError(AppError):
    """Resource not found"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", "NOT_FOUND", 404)


class RateLimitError(AppError):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after} seconds",
            "RATE_LIMIT_EXCEEDED",
            429,
            {"retry_after": retry_after}
        )


class ExternalServiceError(AppError):
    """External service call failed"""
    def __init__(self, service: str, message: str = "Service unavailable"):
        super().__init__(
            f"{service}: {message}",
            "EXTERNAL_SERVICE_ERROR",
            503,
            {"service": service}
        )


def handle_errors(f):
    """Decorator for automatic error handling"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            # Already structured error
            log.error(
                f"Application error: {e.message}",
                code=e.code,
                status_code=e.status_code,
                exc_info=True
            )
            return {
                "success": False,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "status_code": e.status_code,
                    "details": e.details
                }
            }, e.status_code
        except Exception as e:
            # Unexpected error
            log.critical(
                f"Unexpected error: {str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "status_code": 500
                }
            }, 500
    return wrapper


def log_request(f):
    """Decorator to log API requests with timing"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = datetime.utcnow()
        try:
            result = f(*args, **kwargs)
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            
            log.info(
                f"Request completed",
                endpoint=f.__name__,
                duration_ms=round(duration, 2)
            )
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            log.error(
                f"Request failed: {str(e)}",
                endpoint=f.__name__,
                duration_ms=round(duration, 2),
                exc_info=True
            )
            raise
    return wrapper


class ErrorTracker:
    """Track and report errors"""
    
    def __init__(self):
        self.errors: list = []
        self.max_errors = 1000
    
    def track(self, error: Exception, context: Optional[Dict] = None):
        """Track an error with context"""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self.errors.append(error_data)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Log immediately
        log.error(
            f"Tracked error: {str(error)}",
            error_type=type(error).__name__,
            data=context
        )
    
    def get_recent(self, count: int = 10) -> list:
        """Get recent errors"""
        return self.errors[-count:]
    
    def get_stats(self, hours: int = 24) -> Dict:
        """Get error statistics"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        recent = [e for e in self.errors 
                  if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff]
        
        by_type = {}
        for error in recent:
            t = error['type']
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total": len(recent),
            "by_type": by_type,
            "period_hours": hours
        }


# Global error tracker
error_tracker = ErrorTracker()


def setup_global_exception_handling():
    """Setup global exception handlers"""
    
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let keyboard interrupt pass
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        log.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        error_tracker.track(exc_value, {"unhandled": True})
    
    sys.excepthook = handle_unhandled_exception


def get_health_status() -> Dict[str, Any]:
    """Get system health status"""
    import psutil
    
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free // (1024 * 1024 * 1024)
            },
            "errors": error_tracker.get_stats(hours=1)
        }
    except Exception as e:
        log.error(f"Health check failed: {e}")
        return {
            "status": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# Setup on import
setup_global_exception_handling()


"""
Logger Module

This module provides a centralized logging configuration for the entire project
using a singleton pattern to ensure consistent logging across all modules.

Usage:
    from demo-core.utils.logger import Logger
    logger = Logger.get_logger(__name__)

"""

import logging
import sys
import threading
from typing import Optional, Dict
import uuid

class RunIdFilter(logging.Filter):
    """
    Custom logging filter that adds a run_id to each log record.
    
    Args:
        run_id (str): Unique identifier for the current execution run
    """
    def __init__(self, run_id):
        super().__init__()
        self.run_id = run_id

    def filter(self, record):
        record.run_id = self.run_id
        return True

class Logger:
    _loggers: Dict[str, logging.Logger] = {}
    _default_format = '[%(run_id)s] - %(asctime)s - %(levelname)s [%(name)s:%(lineno)s] - %(message)s'
    _default_level = logging.INFO
    _lock = threading.Lock()
    _global_run_id: Optional[str] = None

    @classmethod
    def configure_global_logging(
        cls,
        level: Optional[int] = None,
        log_format: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> None:
        """
        Configure logging globally for the application.
        
        :param level: Global logging level
        :param log_format: Global log format string
        :param run_id: Global run ID for the application
        """
        with cls._lock:
            if level is not None:
                cls._default_level = level
            if log_format is not None:
                cls._default_format = log_format
            if run_id is not None:
                cls._global_run_id = run_id
            
            # Update existing loggers with new configuration
            for logger in cls._loggers.values():
                logger.setLevel(cls._default_level)
                for handler in logger.handlers:
                    handler.setFormatter(logging.Formatter(cls._default_format))
    @classmethod
    def get_logger(
        cls,
        name: str,
        run_id: Optional[str] = None,
        log_level: Optional[int] = None,
        log_format: Optional[str] = None
    ) -> logging.Logger:
        """
        Creates or retrieves a logger with consistent formatting.
        
        :param name: Name of the logger (typically __name__)
        :param run_id: Unique identifier for the current execution run. 
                      If not provided, uses global run_id or generates new one.
        :param log_level: Logging level (defaults to class default)
        :param log_format: Custom log format string (defaults to class default)
        :return: Configured logger instance
        :raises ValueError: If logger name is invalid
        """
        # Validate input parameters
        if not name or not isinstance(name, str):
            raise ValueError("Logger name must be a non-empty string")
            
        # Use provided run_id, global run_id, or generate new one
        effective_run_id = run_id or cls._global_run_id or str(uuid.uuid4())
        
        with cls._lock:
            # Return existing logger if already configured
            if name in cls._loggers:
                return cls._loggers[name]

            # Create new logger
            logger = logging.getLogger(name)
            logger.addFilter(RunIdFilter(effective_run_id))

            # Only configure if the logger doesn't have handlers
            if not logger.handlers:
                formatter = logging.Formatter(log_format or cls._default_format)
                
                # Console handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                
                logger.addHandler(console_handler)
                logger.setLevel(log_level or cls._default_level)

                # Prevent logging from being propagated to the root logger
                logger.propagate = False
                
                # Store in dictionary
                cls._loggers[name] = logger
            
        @classmethod
    def cleanup_loggers(cls) -> None:
        """
        Remove all configured loggers and clear the internal cache.
        Useful for testing or when restarting logging configuration.
        """
        with cls._lock:
            for logger in cls._loggers.values():
                # Remove all handlers
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
            cls._loggers.clear()
            
    @classmethod
    def get_logger_count(cls) -> int:
        """
        Get the number of currently configured loggers.
        
        :return: Number of configured loggers
        """
        with cls._lock:
            return len(cls._loggers)


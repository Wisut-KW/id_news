"""
Logging Agent
Logs errors and events
"""

import os
from datetime import datetime
from typing import Optional


class LoggingAgent:
    """Agent to log errors and events"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file for today
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(logs_dir, f"{today}_errors.log")
    
    def log_error(self, url: str, error_message: str) -> None:
        """
        Log an error with URL
        
        Args:
            url: URL that caused the error
            error_message: Error description
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {url} | {error_message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def log_info(self, message: str) -> None:
        """
        Log an info message
        
        Args:
            message: Info message to log
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | INFO | {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

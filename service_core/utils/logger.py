"""
Shared logger module for the data platform.

Used by Lambda functions (via Lambda Layer) and Glue jobs (via --extra-py-files).
Same import path in both runtimes:

    from service_core.utils.logger import get_logger

Logs are emitted as structured JSON so downstream pipelines (CloudWatch
Logs Insights, Athena, etc.) can query them uniformly across runtimes.
"""

import json
import logging
import os


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def format(self, record):
        return json.dumps(
            {
                "level": record.levelname,
                "service": self.service,
                "message": record.getMessage(),
                "module": record.module,
            }
        )


def get_logger(name: str, service: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service=service))
    logger.addHandler(handler)
    return logger

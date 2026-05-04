"""
Demo Lambda function showing how to consume the shared service_core
module (logger, repositories) via the Lambda Layer published from
service_core/serverless.yml.

The same import path also works inside Glue jobs — see
glue_jobs/hello_world_data_extractor.py.
"""

from service_core.utils.logger import get_logger

logger = get_logger(__name__, service="hello-world")


def handler(event, context):
    logger.info(f"received event: {event}")
    return {"statusCode": 200, "body": "ok"}

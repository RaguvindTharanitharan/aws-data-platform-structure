import json
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler function
    
    Args:
        event: The event data passed to the function
        context: The runtime information of the Lambda function
        
    Returns:
        dict: Response object with status code and body
    """
    try:
        logger.info("Lambda function started")
        logger.info(f"Event: {json.dumps(event)}")
        
        # Extract information from the event if needed
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Your business logic here
        response_body = {
            'message': 'Hello from AWS Lambda!',
            'method': http_method,
            'path': path,
            'query_params': query_params,
            'timestamp': context.aws_request_id
        }
        
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps(response_body)
        }
        
        logger.info("Lambda function completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in Lambda function: {str(e)}")
        
        error_response = {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
        
        return error_response


def health_check_handler(event, context):
    """
    Simple health check endpoint
    
    Args:
        event: The event data passed to the function
        context: The runtime information of the Lambda function
        
    Returns:
        dict: Simple health check response
    """
    logger.info("Health check endpoint called")
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'message': 'Service is running',
            'timestamp': context.aws_request_id
        })
    }

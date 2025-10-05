import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamodbRepository:
    """
    Repository class for DynamoDB operations.
    Provides methods for common DynamoDB table operations including get and put operations.
    """

    def __init__(self, dynamodb_resource=None):
        """
        Initialize the DynamoDB repository.
        
        Args:
            dynamodb_resource: Optional boto3 DynamoDB resource. If not provided, 
                            a new resource will be created.
        """
        self.dynamodb = dynamodb_resource or boto3.resource("dynamodb")

    def get_data_by_id(self, item_name, item_id, item_id_name="id"):
        """
        Retrieves an item from DynamoDB table based on the item ID.
        
        Args:
            item_name (str): The name of the DynamoDB table.
            item_id (str): The ID of the item being queried.
            item_id_name (str): The name of the ID field in the table. Defaults to "id".
            
        Returns:
            dict or None: The item data if found, None if item doesn't exist.
            
        Raises:
            ValueError: If required parameters are missing or invalid.
            ClientError: If DynamoDB operation fails.
        """
        if not item_name or not item_id:
            raise ValueError("item_name and item_id are required")
            
        try:
            logger.info(f"Getting item {item_id} from table {item_name}")
            table = self.dynamodb.Table(item_name)
            response = table.get_item(Key={item_id_name: item_id})
            
            if "Item" not in response:
                logger.info(f"Item {item_id} not found in table {item_name}")
                return None
                
            logger.info(f"Successfully retrieved item {item_id} from table {item_name}")
            return response['Item']
            
        except ClientError as e:
            logger.error(f"Error getting item {item_id} from table {item_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting item {item_id} from table {item_name}: {e}")
            raise

    def put_data(self, item_name, item):
        """
        Puts an item into the DynamoDB table.
        
        Args:
            item_name (str): The name of the DynamoDB table.
            item (dict): The item data to be stored in the table.
            
        Returns:
            dict: The item that was stored.
            
        Raises:
            ValueError: If required parameters are missing or invalid.
            ClientError: If DynamoDB operation fails.
        """
        if not item_name or not item:
            raise ValueError("item_name and item are required")
            
        if not isinstance(item, dict):
            raise ValueError("item must be a dictionary")
            
        try:
            logger.info(f"Putting item into table {item_name}")
            table = self.dynamodb.Table(item_name)
            table.put_item(Item=item)
            logger.info(f"Successfully stored item in table {item_name}")
            return item
            
        except ClientError as e:
            logger.error(f"Error putting item into table {item_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error putting item into table {item_name}: {e}")
            raise
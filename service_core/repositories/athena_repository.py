import boto3
import logging
import time
from typing import Optional, Dict, List, Any, Generator
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AthenaRepository:
    """
    Repository class for Amazon Athena operations.
    Provides methods for executing SQL queries, managing query results, and common Athena operations.
    """

    def __init__(self, athena_client=None, s3_output_location: Optional[str] = None):
        """
        Initialize the Athena repository.
        
        Args:
            athena_client: Optional boto3 Athena client. If not provided, a new client will be created.
            s3_output_location: S3 location for query results. Required for query execution.
        """
        self.athena = athena_client or boto3.client('athena')
        self.s3_output_location = s3_output_location

    def execute_query(
        self,
        query: str,
        database: str,
        output_location: Optional[str] = None,
        workgroup: str = 'primary'
    ) -> str:
        """
        Execute a SQL query in Athena and return the query execution ID.
        
        Args:
            query (str): The SQL query to execute.
            database (str): The Athena database name.
            output_location (str): S3 location for query results. Uses instance default if not provided.
            workgroup (str): Athena workgroup to use. Defaults to 'primary'.
            
        Returns:
            str: The query execution ID.
            
        Raises:
            ValueError: If required parameters are missing or invalid.
            ClientError: If Athena operation fails.
        """
        if not query or not database:
            raise ValueError("query and database are required")
            
        if not isinstance(query, str) or not isinstance(database, str):
            raise ValueError("query and database must be strings")
            
        effective_output_location = output_location or self.s3_output_location
        if not effective_output_location:
            raise ValueError("output_location must be provided either as parameter or instance variable")

        try:
            logger.info(f"Executing query in database {database}")
            
            response = self.athena.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                ResultConfiguration={'OutputLocation': effective_output_location},
                WorkGroup=workgroup
            )
            
            query_execution_id = response['QueryExecutionId']
            logger.info(f"Query execution started with ID: {query_execution_id}")
            
            return query_execution_id
            
        except ClientError as e:
            logger.error(f"Error executing query in database {database}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query in database {database}: {e}")
            raise

    def wait_for_query_completion(
        self,
        query_execution_id: str,
        max_wait_time: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for a query to complete and return the execution details.
        
        Args:
            query_execution_id (str): The query execution ID.
            max_wait_time (int): Maximum time to wait in seconds. Defaults to 300 (5 minutes).
            poll_interval (int): Time between status checks in seconds. Defaults to 2.
            
        Returns:
            dict: Query execution details including status and results.
            
        Raises:
            ValueError: If query_execution_id is invalid.
            TimeoutError: If query doesn't complete within max_wait_time.
            ClientError: If Athena operation fails.
        """
        if not query_execution_id:
            raise ValueError("query_execution_id is required")

        try:
            logger.info(f"Waiting for query {query_execution_id} to complete")
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                response = self.athena.get_query_execution(QueryExecutionId=query_execution_id)
                execution = response['QueryExecution']
                status = execution['Status']['State']
                
                if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                    logger.info(f"Query {query_execution_id} completed with status: {status}")
                    return execution
                    
                logger.debug(f"Query {query_execution_id} status: {status}")
                time.sleep(poll_interval)
            
            raise TimeoutError(f"Query {query_execution_id} did not complete within {max_wait_time} seconds")
            
        except ClientError as e:
            logger.error(f"Error checking query status for {query_execution_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error checking query status for {query_execution_id}: {e}")
            raise

    def get_query_results(
        self,
        query_execution_id: str,
        max_results: int = 1000,
        next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the results of a completed query.
        
        Args:
            query_execution_id (str): The query execution ID.
            max_results (int): Maximum number of results to return. Defaults to 1000.
            next_token (str): Token for pagination. Used to get next page of results.
            
        Returns:
            dict: Query results including data rows and metadata.
            
        Raises:
            ValueError: If query_execution_id is invalid.
            ClientError: If Athena operation fails.
        """
        if not query_execution_id:
            raise ValueError("query_execution_id is required")

        try:
            logger.info(f"Getting results for query {query_execution_id}")
            
            params = {
                'QueryExecutionId': query_execution_id,
                'MaxResults': max_results
            }
            if next_token:
                params['NextToken'] = next_token
                
            response = self.athena.get_query_results(**params)
            
            logger.info(f"Retrieved {len(response.get('ResultSet', {}).get('Rows', []))} rows")
            return response
            
        except ClientError as e:
            logger.error(f"Error getting results for query {query_execution_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting results for query {query_execution_id}: {e}")
            raise

    def execute_query_and_get_results(
        self,
        query: str,
        database: str,
        output_location: Optional[str] = None,
        workgroup: str = 'primary',
        max_wait_time: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a query and wait for results in one operation.
        
        Args:
            query (str): The SQL query to execute.
            database (str): The Athena database name.
            output_location (str): S3 location for query results.
            workgroup (str): Athena workgroup to use. Defaults to 'primary'.
            max_wait_time (int): Maximum time to wait for completion. Defaults to 300 seconds.
            
        Returns:
            dict: Query results including data rows and metadata.
            
        Raises:
            ValueError: If required parameters are missing or invalid.
            TimeoutError: If query doesn't complete within max_wait_time.
            ClientError: If Athena operation fails.
        """
        try:
            # Execute the query
            query_execution_id = self.execute_query(query, database, output_location, workgroup)
            
            # Wait for completion
            execution = self.wait_for_query_completion(query_execution_id, max_wait_time)
            
            # Check if query succeeded
            if execution['Status']['State'] != 'SUCCEEDED':
                error_reason = execution['Status'].get('StateChangeReason', 'Unknown error')
                raise RuntimeError(f"Query failed: {error_reason}")
            
            # Get results
            results = self.get_query_results(query_execution_id)
            
            logger.info(f"Successfully executed query and retrieved results")
            return results
            
        except Exception as e:
            logger.error(f"Error in execute_query_and_get_results: {e}")
            raise

    def get_all_query_results(
        self,
        query_execution_id: str,
        batch_size: int = 1000
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Get all results of a completed query using pagination.
        
        Args:
            query_execution_id (str): The query execution ID.
            batch_size (int): Number of results per batch. Defaults to 1000.
            
        Yields:
            dict: Batches of query results.
            
        Raises:
            ValueError: If query_execution_id is invalid.
            ClientError: If Athena operation fails.
        """
        if not query_execution_id:
            raise ValueError("query_execution_id is required")

        try:
            logger.info(f"Getting all results for query {query_execution_id}")
            next_token = None
            batch_count = 0
            
            while True:
                batch_count += 1
                logger.debug(f"Fetching batch {batch_count} for query {query_execution_id}")
                
                results = self.get_query_results(query_execution_id, batch_size, next_token)
                yield results
                
                # Check if there are more results
                next_token = results.get('NextToken')
                if not next_token:
                    break
                    
            logger.info(f"Completed fetching all results for query {query_execution_id} ({batch_count} batches)")
            
        except Exception as e:
            logger.error(f"Error getting all results for query {query_execution_id}: {e}")
            raise

    def stop_query_execution(self, query_execution_id: str) -> None:
        """
        Stop a running query execution.
        
        Args:
            query_execution_id (str): The query execution ID to stop.
            
        Raises:
            ValueError: If query_execution_id is invalid.
            ClientError: If Athena operation fails.
        """
        if not query_execution_id:
            raise ValueError("query_execution_id is required")

        try:
            logger.info(f"Stopping query execution {query_execution_id}")
            self.athena.stop_query_execution(QueryExecutionId=query_execution_id)
            logger.info(f"Successfully stopped query execution {query_execution_id}")
            
        except ClientError as e:
            logger.error(f"Error stopping query execution {query_execution_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error stopping query execution {query_execution_id}: {e}")
            raise

    def list_databases(self) -> List[str]:
        """
        List all available Athena databases.
        
        Returns:
            list: List of database names.
            
        Raises:
            ClientError: If Athena operation fails.
        """
        try:
            logger.info("Listing Athena databases")
            response = self.athena.list_databases()
            databases = [db['Name'] for db in response.get('DatabaseList', [])]
            logger.info(f"Found {len(databases)} databases")
            return databases
            
        except ClientError as e:
            logger.error(f"Error listing databases: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing databases: {e}")
            raise

    def list_tables(self, database: str) -> List[str]:
        """
        List all tables in a specific database.
        
        Args:
            database (str): The database name.
            
        Returns:
            list: List of table names.
            
        Raises:
            ValueError: If database is invalid.
            ClientError: If Athena operation fails.
        """
        if not database:
            raise ValueError("database is required")

        try:
            logger.info(f"Listing tables in database {database}")
            response = self.athena.list_table_metadata(CatalogName='AwsDataCatalog', DatabaseName=database)
            tables = [table['Name'] for table in response.get('TableMetadataList', [])]
            logger.info(f"Found {len(tables)} tables in database {database}")
            return tables
            
        except ClientError as e:
            logger.error(f"Error listing tables in database {database}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing tables in database {database}: {e}")
            raise

    def get_table_metadata(self, database: str, table: str) -> Dict[str, Any]:
        """
        Get metadata for a specific table.
        
        Args:
            database (str): The database name.
            table (str): The table name.
            
        Returns:
            dict: Table metadata including columns and schema.
            
        Raises:
            ValueError: If database or table is invalid.
            ClientError: If Athena operation fails.
        """
        if not database or not table:
            raise ValueError("database and table are required")

        try:
            logger.info(f"Getting metadata for table {database}.{table}")
            response = self.athena.get_table_metadata(
                CatalogName='AwsDataCatalog',
                DatabaseName=database,
                TableName=table
            )
            logger.info(f"Successfully retrieved metadata for table {database}.{table}")
            return response
            
        except ClientError as e:
            logger.error(f"Error getting metadata for table {database}.{table}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting metadata for table {database}.{table}: {e}")
            raise

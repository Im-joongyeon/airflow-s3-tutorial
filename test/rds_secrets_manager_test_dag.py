"""
RDS Query DAG using AWS Secrets Manager
This DAG connects to RDS using credentials stored in AWS Secrets Manager
and executes a simple query to fetch one record from a table.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import boto3
import json
import pymysql
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def get_secret_from_secrets_manager():
    """
    Retrieve database credentials from AWS Secrets Manager

    Returns:
        dict: Database connection credentials
    """
    import os
    secret_name = os.getenv('RDS_SECRET_NAME', 'real_secret')
    region_name = os.getenv('AWS_REGION', 'ap-northeast-2')

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        logger.info(f"Successfully retrieved secret: {secret_name}")

        # Parse the secret string
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret

    except Exception as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise e


def query_rds_table(**context):
    """
    Connect to RDS and execute a query to fetch one record

    This function:
    1. Retrieves credentials from Secrets Manager
    2. Connects to the MySQL RDS instance
    3. Executes a SELECT query with LIMIT 1
    4. Logs the result
    """
    import os

    # Get database credentials from Secrets Manager
    logger.info("Fetching credentials from Secrets Manager...")
    credentials = get_secret_from_secrets_manager()

    # Extract connection details
    # Get host, port, database from environment variables (not in Secrets Manager)
    host = credentials.get('host') or os.getenv('RDS_HOST', 'real_endpoint')
    username = credentials.get('username')
    password = credentials.get('password')
    database = credentials.get('dbname') or credentials.get('database') or os.getenv('RDS_DATABASE', 'test_db')
    port = credentials.get('port') or int(os.getenv('RDS_PORT', '3306'))

    logger.info(f"Connecting to RDS: {host}:{port}/{database}")

    connection = None
    try:
        # Connect to RDS MySQL
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            database=database,
            port=int(port),
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )

        logger.info("Successfully connected to RDS")

        with connection.cursor() as cursor:
            # Execute query
            query = "SELECT * FROM airbyte_test_users LIMIT 1"
            logger.info(f"Executing query: {query}")

            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                logger.info(f"Query result: {result}")

                # Push result to XCom for downstream tasks
                context['task_instance'].xcom_push(key='query_result', value=result)

                print("=" * 80)
                print("QUERY RESULT:")
                print("=" * 80)
                for key, value in result.items():
                    print(f"{key}: {value}")
                print("=" * 80)

                return result
            else:
                logger.warning("Query returned no results")
                return None

    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise e

    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")


# Create the DAG
with DAG(
    dag_id='rds_secrets_manager_test',
    default_args=default_args,
    description='Test DAG to query RDS using AWS Secrets Manager',
    schedule=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['rds', 'secrets-manager', 'test', 's3-sync'],
) as dag:

    # Task to query RDS
    query_task = PythonOperator(
        task_id='query_rds_with_secrets_manager',
        python_callable=query_rds_table,
        doc_md="""
        ## Query RDS Task

        This task performs the following operations:
        1. Fetches database credentials from AWS Secrets Manager
        2. Connects to the MySQL RDS instance
        3. Executes: `SELECT * FROM airbyte_test_users LIMIT 1`
        4. Logs and returns the result

        ### Requirements
        - AWS credentials configured in Airflow environment
        - IAM permissions for Secrets Manager read access
        - Network connectivity to RDS instance
        - PyMySQL package installed
        """,
    )

    query_task

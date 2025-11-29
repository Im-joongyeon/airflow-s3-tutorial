"""
S3 Sync Test DAG
This DAG is specifically created to test S3 synchronization functionality.
Upload this file to your S3 bucket and verify it appears in Airflow UI.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def print_s3_sync_success():
    """Confirms that S3 sync is working properly"""
    import os
    from datetime import datetime

    print("=" * 60)
    print("🎉 S3 SYNC TEST SUCCESSFUL! 🎉")
    print("=" * 60)
    print(f"DAG execution time: {datetime.now()}")
    print(f"This DAG was synced from S3 bucket!")
    print("=" * 60)
    print("\nEnvironment Variables:")
    print(f"  - S3_BUCKET: {os.getenv('S3_BUCKET', 'Not set')}")
    print(f"  - AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION', 'Not set')}")
    print("=" * 60)
    return "S3 sync is working correctly!"

def test_file_operations():
    """Test file system operations"""
    import os

    print("\nChecking DAG directory contents:")
    dags_dir = "/opt/airflow/dags"
    if os.path.exists(dags_dir):
        files = os.listdir(dags_dir)
        print(f"\nFiles in {dags_dir}:")
        for f in sorted(files):
            file_path = os.path.join(dags_dir, f)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  - {f} ({size} bytes, modified: {mtime})")

    return "File check completed"

with DAG(
    's3_sync_test',
    default_args=default_args,
    description='Test DAG to verify S3 synchronization is working',
    schedule=timedelta(hours=1),  # Runs every hour
    catchup=False,
    tags=['test', 's3-sync', 'verification'],
) as dag:

    # Task 1: Print success message
    test_sync = PythonOperator(
        task_id='verify_s3_sync',
        python_callable=print_s3_sync_success,
    )

    # Task 2: Check files in DAG directory
    check_files = PythonOperator(
        task_id='check_dag_files',
        python_callable=test_file_operations,
    )

    # Task 3: Print system information
    system_info = BashOperator(
        task_id='print_system_info',
        bash_command='''
        echo "=============================="
        echo "System Information"
        echo "=============================="
        echo "Hostname: $(hostname)"
        echo "Date: $(date)"
        echo "Current directory: $(pwd)"
        echo "=============================="
        ''',
    )

    # Task 4: Verify AWS CLI is working
    aws_check = BashOperator(
        task_id='verify_aws_cli',
        bash_command='''
        echo "Checking AWS CLI configuration..."
        if command -v aws &> /dev/null; then
            echo "✓ AWS CLI is installed"
            aws --version
        else
            echo "✗ AWS CLI is not installed"
        fi
        ''',
    )

    # Define task dependencies
    test_sync >> check_files >> system_info >> aws_check

from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator, DatabricksRunNowOperator
from datetime import datetime, timedelta


# Define params for Submit Run Operator
notebook_task = {
    # dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    # Cleaning data and Queries',
    'notebook_path': '/Users/colin.fraser+aicore@gmail.com/test'
}


# Define params for Run Now Operator
notebook_params = {
    "Variable": 5
}


default_args = {
    'owner': 'Colin Fraser',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}


with DAG('0af8d0adfd13_dag',  # I think this is what I'm supposed to do, changed from databricks_dag, which was the filename
         # should be a datetime format
         start_date=datetime(2023, 11, 26),
         # check out possible intervals, should be a string
         schedule_interval='@daily',
         catchup=False,
         default_args=default_args
         ) as dag:

    opr_submit_run = DatabricksSubmitRunOperator(
        task_id='submit_run',
        # the connection we set-up previously
        databricks_conn_id='databricks_default',
        # which cluster do we use? spark.conf.get("spark.databricks.clusterUsageTags.clusterId")
        existing_cluster_id='1108-162752-8okw8dgg',
        notebook_task=notebook_task
    )
    opr_submit_run

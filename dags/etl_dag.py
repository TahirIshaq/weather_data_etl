import os
import json
import pandas as pd
from datetime import datetime
from airflow.decorators import dag, task, task_group
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator
from airflow.providers.amazon.aws.transfers.sql_to_s3 import SqlToS3Operator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator


LATITUDE = "52.5244"
LONGITUDE = "13.4105"
WEATHER_API_ID = "weather_api"
PG_DB_CONN_ID = "dwh"
AWS_CONN_ID = "to_s3"
S3_BUCKET = "weather-data"
BASE_PATH = "/opt/airflow"

default_args = {
    "owner": "Tahir Ishaq",
    "email": "tahirishaq10@gmail.com"
}

@dag(
    dag_id = "etl_weather_data",
    description = "Performs ETL on weather data",
    default_args = default_args,
    start_date = datetime(2024, 10, 22),
    schedule_interval = None,
    catchup = False,
    tags = ["etl", "api"]
)
def elt_weather_data():
    
    is_weather_api_ready = HttpSensor(
        task_id = "is_weather_api_ready",
        http_conn_id = WEATHER_API_ID,
        endpoint = f"/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true"
    )
    
    get_weather_data = SimpleHttpOperator(
        task_id = "get_weather_data",
        http_conn_id = WEATHER_API_ID,
        endpoint = f"/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true",
        method = "GET",
        response_filter = lambda r: json.loads(r.text),
        log_response = True
    )

    @task(task_id="compose_data")
    def compose_data(data):
        """Compose the raw weather data"""
        df = pd.DataFrame(data["current_weather"].values()).transpose()
        df.columns = data["current_weather"].keys()
        df[["latitude", "longitude"]] = data["latitude"] , data["longitude"]
        #print(pd.io.sql.get_schema(df, name="weather_data"))
        #df.to_csv(f"{BASE_PATH}/weather_data.csv")
        return df
    
    @task_group(group_id='create_storage_resources')
    def create_storage_resources():
        # Create weather data table in database
        create_table = SQLExecuteQueryOperator(
            task_id = "create_table",
            conn_id = PG_DB_CONN_ID,
            sql = """
                CREATE TABLE IF NOT EXISTS weather_data (
                    "id" SERIAL,
                    "latitude" REAL, 
                    "longitude" REAL,
                    "time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    "interval" INTEGER,
                    "temperature" REAL,
                    "windspeed" REAL,
                    "winddirection" INTEGER,
                    "is_day" INTEGER,
                    "weathercode" INTEGER
                )
            """
        )

        create_bucket = S3CreateBucketOperator(
            aws_conn_id=AWS_CONN_ID,
            task_id="create_bucket",
            bucket_name=S3_BUCKET,
        )

        create_table >> create_bucket


    get_raw_data = get_weather_data
    compose_weather_data = compose_data(get_raw_data.output)

    @task_group(group_id="update_resources")
    def update_resources():
        # Update weather table
        update_db = SQLExecuteQueryOperator(
            task_id = "update_db",
            conn_id = PG_DB_CONN_ID,
            sql = """
                INSERT INTO weather_data (
                    "latitude", 
                    "longitude", 
                    "time", 
                    "interval", 
                    "temperature", 
                    "windspeed", 
                    "winddirection", 
                    "is_day", 
                    "weathercode"
                ) 
                VALUES(
                    %(latitude)s, 
                    %(longitude)s, 
                    %(time)s, 
                    %(interval)s, 
                    %(temperature)s, 
                    %(windspeed)s, 
                    %(winddirection)s, 
                    %(is_day)s, 
                    %(weathercode)s
                )
            """,
            parameters = { 
                "latitude": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['latitude'][0] }}",
                "longitude": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['longitude'][0] }}",
                "time": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['time'][0] }}",
                "interval": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['interval'][0] }}",
                "temperature": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['temperature'][0] }}",
                "windspeed": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['windspeed'][0] }}",
                "winddirection": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['winddirection'][0] }}",
                "is_day": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['is_day'][0] }}",
                "weathercode": "{{ ti.xcom_pull(task_ids=['compose_data'], key='return_value')[0]['weathercode'][0] }}",
            }
        )

        # update_s3 = LocalFilesystemToS3Operator(
        #     task_id = "update_s3",
        #     aws_conn_id=AWS_CONN_ID,
        #     filename=f"{BASE_PATH}/weather_data.csv",
        #     dest_key="weather_data.csv",
        #     dest_bucket=S3_BUCKET,
        #     replace=True
        # )

        sql_to_s3_task = SqlToS3Operator(
            task_id="sql_to_s3_task",
            sql_conn_id=PG_DB_CONN_ID,
            aws_conn_id=AWS_CONN_ID,
            query="SELECT * FROM weather_data;",
            s3_bucket=S3_BUCKET,
            s3_key="weather_data_test.csv",
            replace=True,
        )

        update_db >> sql_to_s3_task

    # @task(task_id="clean_up")
    # def clean_up():
    #     """Remove any saved files"""
    #     os.remove(f"{BASE_PATH}/weather_data.csv")


    #is_weather_api_ready >> get_composed_data >> create_storage_resources() >> update_resources() >> clean_up()
    is_weather_api_ready >> get_weather_data >> compose_weather_data >> create_storage_resources() >> update_resources()


dag1 = elt_weather_data()

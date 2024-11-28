# Objective
A pipeline that downloads weather [data](https://open-meteo.com/) and store it in postgres and S3.
After selecting the desired city and parameters, a URL will be generated that can used to query the selected parameters of the city selected above.

## How to run the project
```
git clone https://github.com/TahirIshaq/weather_data_elt
cd weather_data_elt
docker compose up -d
In a web browser open: "https://localhost:8080".
Trigger the DAG.
In another tab of the web browser open: "http://localhost:9001".
Check the file that was uploaded to the bucket.
Login to the postgres container by typing the following in the terminal: docker exec -it dwh bash
Login to the postgres server terminal by tying: psql "postgresql://dwh_user:dwh_pass@localhost:5432/dwh_db"
List the current tables in the database: \d
List the weather table schema: \d+ weather_data;
List the contents of weather table: SELECT * FROM weather_data;
Exit the postgres server terminal: type "exit" or ctrl + D
Exit the postgres server container: type "exit" or ctrl + D
Take down all the container: docker compose down
(optional)Take down all the containers, volumes and delete the docker images: docker compose down -v --rmi all
```

## Implementation
In airflow connectors of the destination database, API and AWS S3 need to be created.

## Airflow connection creation
In airfow UI connecitons need to be created for API, postgres and S3.

### Weather data API
Create a HTTP connection type with the following details:
| Key | Value |
| --- | --- |
| Connection Id | weather_api |
| Host | https://api.open-meteo.com |

### Postgres
Create a Postgres connection type with the following details:
| Key | Value |
| --- | --- |
| Connection Id | dwh |
| Host | dwh |
| Port | 5432 |
| Login | dwh_user |
| Password | dwh_pass |
| Database | dwh_db |

### S3
Create a Amazon Web Service connection type with following details:
| Key | Value |
| --- | --- |
| Connection Id | to_s3 |
| AWS Access Key ID | admin |
| AWS Secret Access Key | admin12345 |
| Extra | {"endpoint_url": "http://s3:9000"} |

## Test
```
docker exec -it dwh bash
psql "postgresql://dwh_user:dwh_pass@localhost:5432/dwh_db"
\d
\d+ weather_data
SELECT * FROM weather_data;
```

## To do
- [x] Add DAG test
- [ ] Use Airbyte or similar data loading software
- [ ] Use DBT to perform data transformations

## References
- [Airflow AWS Connection](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/connections/aws.html)
- [Airflow S3 Operator](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/_api/airflow/providers/amazon/aws/operators/s3/index.html#airflow.providers.amazon.aws.operators.s3.S3CreateBucketOperator)
- [Postgres Connection](https://airflow.apache.org/docs/apache-airflow-providers-postgres/stable/connections/postgres.html)
- [HTTP Connection](https://airflow.apache.org/docs/apache-airflow-providers-http/stable/connections/http.html)
- [SQLExecuteQueryOperator dynamic input](https://arthurpedroti.com.br/how-to-create-your-first-etl-in-apache-airflow/)
- [SQLExecuteQueryOperator output](https://www.astronomer.io/blog/apache-airflow-taskflow-api-vs-traditional-operators/)
- [Airflow task groups](https://www.astronomer.io/docs/learn/task-groups/)
- [How to build and automate a python ETL pipeline with airflow on AWS EC2](https://www.youtube.com/watch?v=uhQ54Dgp6To)
- [Apache Airflow One Shot- Building End To End ETL Pipeline Using AirFlow And Astro](https://www.youtube.com/watch?v=Y_vQyMljDsE)
- [repo 1](https://github.com/YemiOla/data_engineering_project_openweathermap_api_airflow_etl_aws)
- [repo 2](https://github.com/krishnaik06/ETLWeather)

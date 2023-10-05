from datetime import datetime
import psycopg2 as db
from elasticsearch import Elasticsearch
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

import pandas as pd

def load_data():
    conn_string = "dbname='airflow' host='postgres' user='airflow' password='airflow'"
    conn = db.connect(conn_string)
    df = pd.read_sql("select * from table_M3", conn)
    df.to_csv('P2M3_harari_netanya_data_raw.csv',index=False)

'''in the load data task, the data will be taken from the database (postgres) based on the query we want'''

def cleaning_data():
    df = pd.read_csv('/opt/airflow/dags/P2M3_harari_netanya_data_raw.csv')
    clean_column = ['gender','enrolled_university','education_level','major_discipline','experience','company_size','company_type','last_new_job']
    df['target'] = df['target'].astype(str) 
    df['target'] = df['target'].str.replace('0.0', 'Loyal') 
    df['target'] = df['target'].str.replace('1.0', 'Tidak Loyal') 

    for i in clean_column:
        mode_value = df[i].mode()[0] # define modus 
        df[i].fillna(mode_value, inplace=True)

    df.to_csv('/opt/airflow/dags/P2M3_harari_netanya_data_clean.csv', index=False)
''' In the data cleaning task, data cleaning will be carried out in the form of:
- fill in missing values in the columns 'gender','enrolled_university','education_level','major_discipline','experience','company_size','company_type','last_new_job'
- replace 1 and 0 in the target column with loyal and tidak loyal'''

def push_es ():
    es = Elasticsearch("elasticsearch:9200") # define elasticsearch ke variable
    df_cleaned=pd.read_csv('/opt/airflow/dags/P2M3_harari_netanya_data_clean.csv') # import csv clean
    for i,r in df_cleaned.iterrows(): # looping untuk masuk ke elastic search
        doc=r.to_json()
        res=es.index(index="data_clean", body=doc)
        print(res)  

'''in the push_es task, the clean data will be connected to elastic search'''

default_args= {
    'owner': 'Neta',
    'start_date': datetime(2023, 9, 29) }

with DAG(
    "Milestone3",
    description='Milestone3',
    schedule_interval='@yearly',
    default_args=default_args, 
    catchup=False) as dag:

    # Task 1
    load_data = PythonOperator(
        task_id='load_data',
        python_callable=load_data

    )

    # Task 2
    cleaning_data = PythonOperator(
        task_id='cleaning_data',
        python_callable=cleaning_data

    )

    #Task 3
    push_es = PythonOperator(
        task_id='push_es',
        python_callable=push_es

    )

    load_data >> cleaning_data >> push_es
# Copyright 2024 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Usage: 
# main.py <data_filepath>

import os, sys
import requests
from google.cloud import bigquery
import json

class URLToBigQuery:
    def __init__(self, data_filepath, gcp_project_id, dataset_id, table_id):
        self.data_filepath = data_filepath
        self.gcp_project_id = gcp_project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.bq_client = bigquery.Client(project=self.gcp_project_id)
    
    def fetch_data(self):
        try:
            with open(data_filepath, 'r') as file:
                data = file.read()
            
            return data
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching data: {e}")
            return None
    
    def load_data_to_bigquery(self, records):
        if records is None or records == []:
            print("No data to load into BigQuery.")
            return
        
        table_ref = self.bq_client.dataset(self.dataset_id).table(self.table_id)
        
        batch_size = 10000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            errors = self.bq_client.insert_rows_json(table_ref, batch)
            
            if errors:
                print(f"Errors occurred while loading data to BigQuery: {errors}")
            else:
                print(f"Batch {i // batch_size + 1} loaded successfully into BigQuery.")
    
    def create_table(self, schema):
        dataset_ref = self.bq_client.dataset(self.dataset_id)
        table_ref = dataset_ref.table(self.table_id)
        
        table = bigquery.Table(table_ref, schema=schema)
        
        try:
            self.bq_client.create_table(table)
            print(f"Table {self.table_id} created successfully.")
        except Exception as e:
            print(f"An error occurred while creating the table: {e}")
    
    def process(self):
        data = self.fetch_data()
        if data is not None:
            records = data.split('\n')
            jrecords = []
            counter = 0
            for record in records:
                try:
                    record_clean = json.loads(record.replace('null','"null"'))
                    
                    jpayload = {
                        'id': f"{record_clean['id']}",
                        'type': f"{record_clean['type']}",
                        'title': f"{record_clean['attributes']['title']}",
                        'lang': f"{record_clean['attributes']['lang']}",
                        'createdAt': f"{record_clean['attributes']['createdAt']}",
                        'updatedAt': f"{record_clean['attributes']['updatedAt']}",
                        'publishedAt': f"{record_clean['attributes']['publishedAt']}",
                        'slug': f"{record_clean['attributes']['slug']}",
                        'hash': f"{record_clean['attributes']['hash']}",
                        #'htmlBody': f"{record_clean['attributes']['htmlBody']}",
                        'desc': '' if record_clean['attributes']['metaDescription']==[] else f"{record_clean['attributes']['metaDescription']}",
                        'keywords': f"{record_clean['attributes']['article']['metaKeywords']}",
                        'url': f"https://support.com/en_us/'{record_clean['attributes']['slug']}-{record_clean['attributes']['hash']}" # TODO Update URL Prefix
                    }
                    
                    jrecords.append(jpayload)
                except Exception as e:
                    print(f'[ EXCEPTION ] Unable to parse record. {e}. {record}\n')
            
            return jrecords


if __name__=='__main__':
    data_filepath = sys.argv[1]
    gcp_project_id = os.environ.get('GCP_PROJECT_ID','gcp_project_id_not_set')
    dataset_id = 'lunar_data_ds'  # TODO: Create BQ Dataset
    table_id = 'articledata'
    loader = URLToBigQuery(data_filepath, gcp_project_id, dataset_id, table_id)
    processed_records = loader.process()
    schema = [
        bigquery.SchemaField("id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lang", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("createdAt", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("updatedAt", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("publishedAt", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("slug", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("hash", "STRING", mode="NULLABLE"),
        #bigquery.SchemaField("htmlBody", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("desc", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("keywords", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
    ]
    loader.create_table(schema=schema)
    loader.load_data_to_bigquery(processed_records)
    print(f'Complete')

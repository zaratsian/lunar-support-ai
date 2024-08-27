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
# main.py <url>

import os, sys
import requests
from google.cloud import bigquery
import json

class URLToBigQuery:
    def __init__(self, url, gcp_project_id, dataset_id, table_id):
        self.url = url
        self.gcp_project_id = gcp_project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.bq_client = bigquery.Client(project=self.gcp_project_id)
    
    def fetch_data(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.json()
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
        json_data = self.fetch_data()
        if json_data is not None:
            if isinstance(json_data, dict):
                records = json_data['playContentArray']['playContents']
                processed_records = []
                for r in records:
                    jpayload = {
                        'contentId': f"{r.get('contentId')}",
                        'mediaId': f"{r.get('mediaId','')}",
                        'title': f"{r.get('title')}",
                        'runtime': f"{r.get('runtime','')}",
                        'formattedRuntime': f"{r.get('formattedRuntime')}",
                        'logLine': f"{r.get('logLine')}",
                        'releaseYear': f"{r.get('releaseYear')}",
                        'studioId': f"{r.get('studioId')}",
                        'actors': f"{r.get('actors')}",
                        'directors': f"{r.get('directors')}",
                        'genres': f"{r.get('genres')}",
                        'categories': f"{r.get('categories')}",
                    }
                    processed_records.append(jpayload)
                
                #self.load_data_to_bigquery(processed_records)
                return processed_records


if __name__=='__main__':
    url = sys.argv[1]
    gcp_project_id = os.environ.get('GCP_PROJECT_ID','gcp_project_id_not_set')
    dataset_id = 'lunar_data_ds'  # TODO: Create BQ Dataset
    table_id = 'webdata'
    loader = URLToBigQuery(url, gcp_project_id, dataset_id, table_id)
    processed_records = loader.process()
    schema = [
        bigquery.SchemaField("contentId", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("mediaId", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("runtime", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("formattedRuntime", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("logLine", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("releaseYear", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("studioId", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("actors", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("directors", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("genres", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("categories", "STRING", mode="NULLABLE"),
    ]
    loader.create_table(schema=schema)
    loader.load_data_to_bigquery(processed_records)
    print(f'Complete')

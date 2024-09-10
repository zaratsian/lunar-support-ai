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

import sys, os
import logging
from google.cloud import bigquery

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

class BQClient:
    def __init__(self):
        self.bq_client = bigquery.Client()
        self.embedding_model_name = os.environ.get('EMBEDDING_MODEL_NAME','')
    
    def query(self, user_query, table_id):
        print(f'Querying BigQuery Table: {table_id}')

        query = f'''
with query_embeddings as (
    select ml_generate_embedding_result from 
    ML.GENERATE_EMBEDDING(MODEL `lunar_data_ds.{self.embedding_model_name}`,
        (select "{user_query}" as content),
        STRUCT(TRUE as flatten_json_output)
    )
),
top_matches as (
  select 
    * except (ml_generate_embedding_result),
    ML.DISTANCE(
      s.text_embedding, 
      q.ml_generate_embedding_result, 
      'COSINE') as distance
  from
    `lunar_data_ds.{table_id}` s,
    query_embeddings q
  order by 
    distance ASC
  limit 20
)

select * except (distance)
from top_matches
order by distance ASC
        '''

        logging.debug(f'BigQuery query: {query}')

        rows = self.bq_client.query_and_wait(query)
        results = [r for r in rows]
        return results
    
    def _general_query(self, query_str):
        rows = self.bq_client.query_and_wait(query_str)
        results = [r for r in rows]
        return results

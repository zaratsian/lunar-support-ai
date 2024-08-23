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

import sys
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
    
    def query(self, user_query, dataset_id, table_id, bq_embeddings_model):
        
        query = f'''
with query_embeddings as (
    select text_embedding from 
    ML.GENERATE_TEXT_EMBEDDING(MODEL `{dataset_id}.{bq_embeddings_model}`,
        (select "{user_query}" as content),
        STRUCT(TRUE as flatten_json_output)
    )
),
top_matches as (
  select 
    s.title, s.logLine, s.releaseYear,
    ML.DISTANCE(
      s.text_embedding,
      q.text_embedding,
      'COSINE') as distance
  from
    `{dataset_id}.{table_id}` s,
    query_embeddings q
  order by 
    distance ASC
  limit 20
)

select *
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


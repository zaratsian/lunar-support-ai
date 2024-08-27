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

# Reference: https://cloud.google.com/bigquery/docs/generate-text-embedding#bq

export GCP_PROJECT_NUMBER=$(gcloud projects list \
--filter="$(gcloud config get-value project)" \
--format="value(PROJECT_NUMBER)")

# Create BQ Connection
bq mk --connection --location=$GCP_REGION --project_id=$GCP_PROJECT_ID \
    --connection_type=CLOUD_RESOURCE ${BQ_CONNECTION_ID}

# Show Connection
bq show --connection ${GCP_PROJECT_ID}.${GCP_REGION}.${BQ_CONNECTION_ID}

# Extract Service Account
export MEMBER=$(bq show --connection ${GCP_PROJECT_ID}.us-central1.bqml-embedding | grep "serviceAccountId" | awk -F'"' '{print $4}')

# Grant the connection's service account the Vertex AI User role.
gcloud projects add-iam-policy-binding '${GCP_PROJECT_NUMBER}' --member='serviceAccount:${MEMBER}' --role='roles/aiplatform.user' --condition=None

# Create Embeddings Model
bq query --use_legacy_sql=false "
CREATE OR REPLACE MODEL \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.${EMBEDDING_MODEL_NAME}\`
REMOTE WITH CONNECTION \`${BQ_CONNECTION_ID}\`
OPTIONS (ENDPOINT = 'text-embedding-004'
);"

# Generate text embeddings for web data
bq query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.webdata_embeddings\` AS (
  SELECT 
    * except (ml_generate_embedding_result, ml_generate_embedding_statistics, ml_generate_embedding_status),
    ml_generate_embedding_result as text_embedding
  FROM ML.GENERATE_EMBEDDING(
    MODEL \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.${EMBEDDING_MODEL_NAME}\`,
    (SELECT *, CONCAT(title, ' | ', logLine, ' | ', actors, ' | ', directors, ' | ', genres, ' | ', categories) as content FROM \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.webdata\`),
    STRUCT(TRUE AS flatten_json_output)
  )
);"

# Generate text embeddings for article data
bq query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.articledata_embeddings\` AS (
  SELECT 
    * except (ml_generate_embedding_result, ml_generate_embedding_statistics, ml_generate_embedding_status),
    ml_generate_embedding_result as text_embedding
  FROM ML.GENERATE_EMBEDDING(
    MODEL \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.${EMBEDDING_MODEL_NAME}\`,
    (SELECT *, CONCAT(title, ' | ', \`desc\`) as content FROM \`${GCP_PROJECT_ID}.${BQ_DATASET_ID}.articledata\`),
    STRUCT(TRUE AS flatten_json_output)
  )
);"

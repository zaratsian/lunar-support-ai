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

# Check env var
if [ -z "${GCP_PROJECT_ID}" ]; then
    echo "GCP_PROJECT_ID is not set or is empty. Run the .env to set the env variable, then try again."
    exit 1
else
    echo "GCP_PROJECT_ID is set to '${GCP_PROJECT_ID}'"
fi

# Check env var
if [ -z "${GCP_REGION}" ]; then
    echo "GCP_REGION is not set or is empty. Run the .env to set the env variable, then try again."
    exit 1
else
    echo "GCP_REGION is set to '${GCP_REGION}'"
fi

gcloud run deploy lunar-support-ai-ui \
--source src \
--region $GCP_REGION \
--platform managed \
--min-instances 0 \
--max-instances 3 \
--cpu 1 \
--memory 512Mi \
--timeout 20 \
--session-affinity \
--set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID \
--set-env-vars GCP_REGION=$GCP_REGION \
--set-env-vars BRAND=$BRAND \
--set-env-vars BRAND_LOGO_IMG=$BRAND_LOGO_IMG \
--set-env-vars APP_BACKGROUND_IMG=$APP_BACKGROUND_IMG \
--allow-unauthenticated

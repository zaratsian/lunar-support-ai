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

import os
import json
from flask import Flask, render_template, request, jsonify
from modules import llm, prompt_template, utils, bq

app = Flask(__name__)

gcp_project_id = os.environ.get('GCP_PROJECT_ID','')
gcp_region = os.environ.get('GCP_REGION','')
brand_name = os.environ.get('BRAND','')

llm_client = llm.GCP_GenAI(GCP_PROJECT_ID=gcp_project_id, GCP_REGION=gcp_region)
bq_obj = bq.BQClient()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # Extract data from the request payload
    data = request.json
    user_comment = data.get('user_comment', '')
    chat_history = data.get('chat_history', [])

    try:
        llm_route = llm_client.call_gemini(prompt=prompt_template.prompt_router.format(
            user_comment=user_comment,
            brand=brand_name
        ))

        print(f'llm route: {llm_route}')

        # Get Catalog Info
        if llm_route in ['recommendations','media']:
            catalog_results = bq_obj.video_query(user_query=user_comment)
        else:
            catalog_results = ''

        # LLM Response
        llm_response = llm_client.call_gemini(prompt=prompt_template.prompt_recommendations.format(
            user_comment=user_comment,
            brand=brand_name,
            chat_history=json.dumps(chat_history),
            catalog=catalog_results
        ))
        llm_response = utils.format_summary(llm_response)
        agent_response = f"{llm_response}"

        # Chat History
        chat_history.append({"user": user_comment, "agent": agent_response})

        # Response Payload
        response_payload = {
            "agent_response": agent_response,
            "chat_history": chat_history
        }
    except Exception as e:
        print(f'[ EXCEPTION ] {e}')

        # LLM Response
        llm_response = llm_client.call_gemini(prompt=prompt_template.prompt_recommendations.format(
            user_comment=user_comment,
            brand=brand_name,
            chat_history=json.dumps(chat_history),
            catalog='',
        ))
        llm_response = utils.format_summary(llm_response)
        agent_response = f"{llm_response}"

        # Chat History
        chat_history.append({"user": user_comment, "agent": agent_response})

        # Response Payload
        response_payload = {
            "agent_response": agent_response,
            "chat_history": chat_history
        }

    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(port=8080, debug=True)


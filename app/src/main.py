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
import re
from flask import Flask, render_template, request, jsonify
from modules import llm, prompt_template, utils, bq

app = Flask(__name__)

gcp_project_id = os.environ.get('GCP_PROJECT_ID','')
gcp_region = os.environ.get('GCP_REGION','')
brand = os.environ.get('BRAND','')

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
            user_comment=user_comment
        )).strip()
        print(f'llm route: {llm_route}')

        # Retrieve Knowledge Base
        if llm_route in ['recommendations','media']:
            print(f'Retrieving Media Knowledge Base')
            catalog_results = bq_obj.query(user_query=user_comment, table_id='webdata_embeddings')

            catalog_results_processed = ''
            for catalog_result in catalog_results:
                for k,v in dict(catalog_result).items():
                    if k in ['releaseYear', 'runtime', 'mediaId', 'logLine', 'contentType', 'studio', 'title', 'content']:
                        if k == 'content':
                            json_content = json.loads(dict(catalog_result)['content'])
                            for k2,v2 in json_content.items():
                                if k2 in ['minReleaseYear','maxReleaseYear','studio','formattedEpisodeCount','formattedSeasonCount']:
                                    catalog_results_processed += f'{k2}:\t{v2}\n'
                                elif k2 in ['childContent']:
                                    match = re.search(r"'episodeLabel':\s*'([^']+)'", f"{json_content['childContent'][0]}")
                                    if match:
                                        catalog_results_processed += f'episodeLabel:\t{match.group(1)}\n'

                        else:
                            catalog_results_processed += f'{k}:\t{v}\n'
                
                catalog_results_processed += '\n'

            prompt=prompt_template.prompt_persona.format(brand=brand) + '\n' + prompt_template.prompt_media.format(
                user_comment=user_comment,
                chat_history=json.dumps(chat_history),
                knowledge_base=catalog_results_processed,
                brand=brand
            )
        elif llm_route in ['cancellation','payments','login']:
            print(f'Retrieving Article Knowledge Base')
            catalog_results = bq_obj.query(user_query=user_comment, table_id='articledata_embeddings')
            catalog_results = '\n'.join([json.dumps(dict(c)) for c in catalog_results])

            prompt=prompt_template.prompt_persona.format(brand=brand) + '\n' + prompt_template.prompt_support.format(
                user_comment=user_comment,
                chat_history=json.dumps(chat_history),
                knowledge_base=catalog_results,
                brand=brand
            )
        else:
            prompt=prompt_template.prompt_persona.format(brand=brand) + '\n' + prompt_template.prompt_support.format(
                user_comment=user_comment,
                chat_history=json.dumps(chat_history),
                knowledge_base='',
                brand=brand
            )

        # LLM Response
        print(f'Prompt: {prompt}')
        llm_response = llm_client.call_gemini(prompt)
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
        prompt=prompt_template.prompt_persona.format(brand=brand) + '\n' + prompt_template.prompt_media.format(
            user_comment=user_comment,
            chat_history=json.dumps(chat_history),
            knowledge_base=''
        )
        llm_response = llm_client.call_gemini(prompt)
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

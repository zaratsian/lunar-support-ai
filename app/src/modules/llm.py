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
import json
import vertexai
import logging
from vertexai.generative_models import GenerativeModel, GenerationConfig, Tool, HarmCategory, HarmBlockThreshold, SafetySetting
from vertexai.language_models import TextGenerationModel
from vertexai.preview.generative_models import grounding

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

class GCP_GenAI:

    def __init__(self, GCP_PROJECT_ID, GCP_REGION):
        if GCP_PROJECT_ID=="":
            logging.warning(f'GCP_PROJECT_ID ENV variable is empty. Be sure to set the GCP_PROJECT_ID ENV variable.')
        
        if GCP_REGION=="":
            logging.warning(f'GCP_REGION ENV variable is empty. Be sure to set the GCP_REGION ENV variable.')
        
        self.GCP_PROJECT_ID = GCP_PROJECT_ID
        self.GCP_REGION = GCP_REGION
        self.vertexai_obj = vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)

    def call_gemini(self, 
        prompt,
        model_id='gemini-1.5-flash-001',
        temperature=0.5, 
        max_output_tokens=1024, 
        top_p=0.8,
        top_k=40, 
        stop_sequences=None, 
        safety_settings=None,
        return_raw=False,
        ground_in_google_search=False,
        ):
        '''
            The Vertex AI Gemini API supports multimodal prompts as input and ouputs text or code.
            https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini
            https://cloud.google.com/vertex-ai/docs/generative-ai/multimodal/send-chat-prompts-gemini
        '''
        try:
            # Initialize Model
            logging.info(f'Calling Gemini model {model_id}')
            llm_model_gemini = GenerativeModel(model_id)

            safety_config = [
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
            ]

            if ground_in_google_search:

                # Use Google Search for grounding
                tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

                response = llm_model_gemini.generate_content(
                    contents=prompt,
                    tools=[tool],
                    generation_config=GenerationConfig(
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        candidate_count=1,
                        max_output_tokens=max_output_tokens,
                        stop_sequences=stop_sequences,
                    ),
                    safety_settings=safety_config
                )

            else:
                response = llm_model_gemini.generate_content(
                    contents=prompt,
                    generation_config=GenerationConfig(
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        candidate_count=1,
                        max_output_tokens=max_output_tokens,
                        stop_sequences=stop_sequences,
                    ),
                    safety_settings=safety_config
                )

            logging.info(f'Gemini LLM response: {response}')

            if not return_raw:
                response = response.candidates[0].content.parts[0].text

            return response
        except Exception as e:
            logging.exception(f'At call_gemini. {e}')
            return ''

    def call_palm_text(self,
        prompt,
        temperature=0.5,
        max_output_tokens=1024,
        top_p=0.8,
        top_k=40,
        return_raw=False  # Returns raw llm response
        ):
        try:
            parameters = {
                "temperature": temperature,  # Temperature controls the degree of randomness in token selection.
                "max_output_tokens": max_output_tokens,  # Token limit determines the maximum amount of text output.
                "top_p": top_p,  # Tokens are selected from most probable to least until the sum of their probabilities equals the top_p value.
                "top_k": top_k,  # A top_k of 1 means the selected token is the most probable among all tokens.
            }

            llm_model_palm_text = TextGenerationModel.from_pretrained("text-bison")
            response = llm_model_palm_text.predict(prompt,
                **parameters,
            )

            if not return_raw:
                response = (response.text).replace('"','').replace("'",'').strip()

            return response
        except Exception as e:
            logging.exception(f'At call_palm_text. {e}')
            return ''

    def text_embedding(self, input_list, google_embeddings_model='text-embedding-004') -> list:
        '''
        Available Embeddings Models:
        https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versioning#stable-versions-available.md
        
        input_list = [
            'Who founded Google',
        ]
        '''
        model = TextEmbeddingModel.from_pretrained(google_embeddings_model)
        embeddings = model.get_embeddings(input_list)
        for embedding in embeddings:
            vector = embedding.values
        return vector

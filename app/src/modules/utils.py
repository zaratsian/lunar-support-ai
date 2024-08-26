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
import re

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

def format_summary(input:str):
    formatted_str = input.replace('\n','<br>')

    formatted_str = formatted_str.replace('User:','').replace('Agent:','').replace('user:','').replace('agent:','').strip()
    
    while '**' in formatted_str:
        formatted_str = formatted_str.replace('**', '<b>', 1)
        formatted_str = formatted_str.replace('**', '</b>', 1)
    
    return formatted_str

def format_summary_for_speech(input_str):
    formatted_str = re.sub('(\n|\t|\r)',' ', input_str)
    formatted_str = re.sub('[^a-zA-Z0-9 \\.\\!\\?\\,\']',' ', formatted_str)
    return formatted_str

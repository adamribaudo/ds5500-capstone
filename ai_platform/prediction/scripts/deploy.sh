#!/bin/bash

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# This has to be run after train-cloud.sh is successfully executed

#gcloud components install beta
export MODEL_VERSION=v1
export MODEL_NAME='test_sk'
MODEL_DIR=gs://example3w/lr_2/2
CUSTOM_ROUTINE_PATH=gs://${BUCKET_NAME}/lr_2/library/custom_routine-1.0.tar.gz

FRAMEWORK=SCIKIT_LEARN

echo "First, creating the model resource..."
gcloud beta ai-platform models create ${MODEL_NAME} --regions=${REGION} \
  --enable-logging --enable-console-logging

echo "Second, creating the model version..."
gcloud beta ai-platform versions create ${MODEL_VERSION} \
  --model=${MODEL_NAME} \
  --origin=${MODEL_DIR}/model/ \
  --framework=${FRAMEWORK} \
  --runtime-version=${RUNTIME_VERSION} \
  --python-version=${PYTHON_VERSION} \
  --package-uris=${CUSTOM_ROUTINE_PATH} \

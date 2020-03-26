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

export MODEL_VERSION=v1
export MODEL_NAME='test_sk'
export MODEL_DIR="gs://example3w/lr/3"
# export MACHINE_TYPE="machine used for testing"

FRAMEWORK=SCIKIT_LEARN

# create the model resource for deploying
echo "First, creating the model resource..."
gcloud ai-platform models create ${MODEL_NAME} --regions=${REGION}

# create the model version and load the model used for prediciton to this version
echo "Second, creating the model version..."
gcloud ai-platform versions create ${MODEL_VERSION} \
  --model ${MODEL_NAME} \
  --origin ${MODEL_DIR}/model \
  --framework ${FRAMEWORK} \
  --runtime-version=${RUNTIME_VERSION} \
  --python-version=${PYTHON_VERSION} \
# --machineType=${MACHINE_TYPE}

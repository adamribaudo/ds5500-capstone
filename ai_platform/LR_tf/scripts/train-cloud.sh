#!/bin/bash
#
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
# Runs a training job in AI platform.
set -euxo pipefail

echo "Submitting an AI Platform job..."

MODEL_NAME="tensorflow_test" # change to your model name

PACKAGE_PATH=./trainer # This can be a GCS location to a zipped and uploaded package
MODEL_DIR=gs://${BUCKET_NAME}/tensorflow_test/model/${MODEL_NAME}

CURRENT_DATE=`date +%Y%m%d_%H%M%S`
JOB_NAME=train_${MODEL_NAME}_${CURRENT_DATE}


gcloud ai-platform jobs submit training ${JOB_NAME} \
        --stream-logs \
        --job-dir=${MODEL_DIR} \
        --runtime-version=${RUNTIME_VERSION} \
        --python-version=${PYTHON_VERSION} \
        --region=${REGION} \
        --module-name=trainer.input \
        --package-path=${PACKAGE_PATH}  \
        --config=./config.yaml \


# Notes:
# use --packages instead of --package-path if gcs location
# add --reuse-job-dir to resume training

#!/bin/bash

# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Exports variables for project setup.
# set -euxo pipefail


function err() {
  echo "ERROR: $*" >&2
  return 1
}

function export_variables(){
    # Preset environment variables. You may use them without changing:
    export RUNTIME_VERSION=1.15
    export PYTHON_VERSION=3.7
    export REGION=us-central1

    # UNCOMMENT & REPLACE "your-gcp-project-id" with your GCP PROJECT ID
    export PROJECT_ID="amiable-octane-267022"
    #"ds5500"

    # UNCOMMENT & REPLACE "your-gcp-bucket-name" with a universally
    # unique name for a GCS bucket. Do not include gs://
    export BUCKET_NAME="example3w"
    #"beam"

    # UNCOMMENT & REPLACE "path/to/service/account/key" with the full path to
    # the service account key file which you have created and downloaded.
    export GOOGLE_APPLICATION_CREDENTIALS="/Users/wangzhengye/Desktop/ai_platform/training/LR_sk/amiable-octane-267022-061a6f297eeb.json"
    #"/Users/wangzhengye/Desktop/ai_platform/training/LR_sk/ds5500-7e5f8aa07468.json"


    echo "RUNTIME_VERSION='${RUNTIME_VERSION}'"
    echo "PYTHON_VERSION='${PYTHON_VERSION}'"
    echo "REGION='${REGION}'"

    if [[ -z ${PROJECT_ID} || ${PROJECT_ID} == "your-gcp-project-id" ]]; then
      err "Please set PROJECT_ID to your GCP Project ID"
    else
      echo "PROJECT_ID='${PROJECT_ID}'"
    fi

    if [[ -z ${BUCKET_NAME} || ${BUCKET_NAME} == "your-gcs-bucket-name" ]]; then
      err "Please set BUCKET_NAME to an existing GCS bucket"
    else
      echo "BUCKET_NAME='${BUCKET_NAME}'"
    fi

    if [[ -z ${GOOGLE_APPLICATION_CREDENTIALS} || ${GOOGLE_APPLICATION_CREDENTIALS} == "path/to/service/account/key.json" ]]; then
      err "Please set GOOGLE_APPLICATION_CREDENTIALS to the path to your service account key"
    else
      echo "GOOGLE_APPLICATION_CREDENTIALS='${GOOGLE_APPLICATION_CREDENTIALS}'"
    fi
}

main(){
    export_variables || err "Unable to set variables"
}

main "$@"

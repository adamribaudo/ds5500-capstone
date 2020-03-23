#!/usr/bin/env python
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
from setuptools import find_packages
from setuptools import setup

REQUIRED_PACKAGES = [
    'tensorflow==2.1.0',
    'protobuf>=3.8.0',
    'pyarrow==0.15.1',
    'pytz>=2018.3',
    'tensorflow-model-analysis>=0.15.4',
    'tensorflow-io==0.12.0',
    'grpcio==1.24.3',
    'absl-py==0.7',
    'python-dateutil<3,>=2.8.0',
    'avro-python3==1.8.1',
    'pandas-gbq==0.11.0',
    'google-cloud-bigquery==1.16.0',
    'google-cloud-bigquery-storage==0.7.0',
    'google-cloud-core>=1.0.0'
]

setup(
    name='trainer',
    description='AI Platform Training job for TensorFlow',
    author='Google Cloud Platform',
    install_requires=REQUIRED_PACKAGES,
    version='0.1',
    packages=find_packages(),
    include_package_data=True
)

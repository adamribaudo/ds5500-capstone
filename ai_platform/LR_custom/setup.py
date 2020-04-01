#!/usr/bin/env python
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

REQUIRED_PACKAGES = [
                     'tensorflow==1.15.2',
                     'scikit-learn>=0.20.2',
                     'pandas==0.24.2',
                     'cloudml-hypertune',
                     'pandas-gbq==0.11.0',
                     'google-cloud-bigquery==1.16.0',
                     'google-cloud-bigquery-storage==0.7.0',
                     'google-cloud-core>=1.0.0'
                     ]


import setuptools
setuptools.setup(name='custom_routine',
                 packages=['trainer'],
                 version="1.0",
                 install_requires=REQUIRED_PACKAGES,
                 )

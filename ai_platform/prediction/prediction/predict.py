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

import os
import logging
import pandas
import googleapiclient.discovery
import numpy as np

logging.basicConfig()

# the data would like to predict
def read_from_bigquery(full_table_path,project_id):
    """Read data from BigQuery
        
        Args:
        full_table_path: (string) full path of the table containing training data
        in the format of [project_id.dataset_name.table_name].
        project_id: the GCP project this tabel belongs to
        """
    sql="""SELECT * FROM `{table}`""".format(table=full_table_path)
    df = pandas.read_gbq(sql,project_id=project_id,dialect='standard')
    return df

def _feature_label_split(data_df, label_column,unused_column):
    """Split the DataFrame into features and label respectively.
        Args:
        data_df: (pandas.DataFrame) DataFrame the splitting to be performed on
        label_column: (string) name of the label column
        Returns:
        A Tuple of (pandas.DataFrame, pandas.Series)
        """
    return data_df.loc[:, (data_df.columns != label_column) & (data_df.columns != unused_column)], data_df[label_column]

df_test = read_from_bigquery("amiable-octane-267022.kkbox.output_train_1","amiable-octane-267022")
X_test, y_test =_feature_label_split(df_test,"is_churn","msno")
instances=[
           np.array(X_test.iloc[0,:])

]

PROJECT_ID = os.getenv('PROJECT_ID')
MODEL_NAME = os.getenv('MODEL_NAME')
MODEL_VERSION = os.getenv('MODEL_VERSION')

logging.info('PROJECT_ID: %s', PROJECT_ID)
logging.info('MODEL_NAME: %s', MODEL_NAME)
logging.info('MODEL_VERSION: %s', MODEL_VERSION)

service = googleapiclient.discovery.build('ml', 'v1',cache_discovery=False)
name = 'projects/{}/models/{}/versions/{}'.format(PROJECT_ID, MODEL_NAME,
                                                  MODEL_VERSION)

response = service.projects().predict(name=name,body={'instances': instances}).execute()

if 'error' in response:
    logging.error(response['error'])
else:
    print(response['predictions'])

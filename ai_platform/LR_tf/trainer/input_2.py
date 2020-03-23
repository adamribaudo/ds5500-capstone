
"""Load Data"""
# https://www.tensorflow.org/io/tutorials/bigquery
# https://codelabs.developers.google.com/codelabs/fraud-detection-with-bigquery-and-tensorflow-enterprise/index.html?index=..%2F..index#3

#from __future__ import absolute_import
#from __future__ import division
#from __future__ import print_function

import tensorflow as tf
import os
import logging

from tensorflow.python.framework import ops
from tensorflow.python.framework import dtypes
from tensorflow_io.bigquery import BigQueryClient
from tensorflow_io.bigquery import BigQueryReadSession
from google.cloud import bigquery
from oauth2client.service_account import ServiceAccountCredentials

from tensorflow import feature_column





from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras import regularizers
from tensorflow.keras import backend as K


key_path = "amiable-octane-267022-061a6f297eeb.json"

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gs://example3w/amiable-octane-267022-061a6f297eeb.json"


credentials_dict = {
# put the credentials directly here
}


PROJECT_ID = "amiable-octane-267022"
TABLE_NAME = "Member_2"
DATASET_ID = DATASET_ID = 'census_dataset'
BATCH_SIZE=32

SCHEMA = [bigquery.SchemaField("msno", "STRING"),
          bigquery.SchemaField("bd", "FLOAT64"),
          bigquery.SchemaField("gender_male", "STRING"),
          bigquery.SchemaField("gender_unknown", "STRING"),
          bigquery.SchemaField("reg_days_scaled", "FLOAT64"),
          bigquery.SchemaField("is_churn", "STRING"),
          ]

UNUSED_COLUMNS=["msno"]

def transofrom_row(row_dict):
    # get all independent features
    feature_dict = {column:tensor
        for (column,tensor) in row_dict.items()
        }

    # Extract feature column
    is_churn = feature_dict.pop('is_churn')
    
    # Convert feature column to 0.0/1.0
    is_churn_float = tf.cond(tf.equal(tf.strings.strip(is_churn), '1.0'),
                             lambda: tf.constant(1.0),
                             lambda: tf.constant(0.0))
    return (feature_dict, is_churn_float)

def read_bigquery(table_name):
    """Read data from Google Big Query
        
        Args:
        table_name: (string) name of the table
        
        Returns:
        A tensorflow dataset
        """

#    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict)

    tensorflow_io_bigquery_client = BigQueryClient()
    read_session = tensorflow_io_bigquery_client.read_session("projects/" + PROJECT_ID,
                                                              PROJECT_ID, table_name, DATASET_ID,
                                                              selected_fields=list(field.name for field in SCHEMA if not field.name in UNUSED_COLUMNS),
                                                              output_types = list(dtypes.double if field.field_type == 'FLOAT64'
                                                                                  else dtypes.string for field in SCHEMA
                                                                                  if not field.name in UNUSED_COLUMNS),
                                                              requested_streams=2)
        
    dataset = read_session.parallel_read_rows()
    transformed_ds = dataset.map(transofrom_row)
    return transformed_ds




"""Format the columns"""
Categorical_Features=[
                      'gender_male',
                      'gender_unknown',]
Numeric_Features=['bd','reg_days_scaled']

def get_categorical_feature_values(column):
    query = 'SELECT DISTINCT {} FROM `{}`.{}.{}'.format(column, PROJECT_ID, DATASET_ID, TABLE_NAME)
    client = bigquery.Client(project=PROJECT_ID)
    dataset_ref = client.dataset(DATASET_ID)
    job_config = bigquery.QueryJobConfig()
    query_job = client.query(query, job_config=job_config)
    result = query_job.to_dataframe()
    return result.values[:,0]

def format_features():
    feature_columns = []
    
    # categorical cols
    for header in Categorical_Features:
        categorical_feature = feature_column.categorical_column_with_vocabulary_list(header, get_categorical_feature_values(header))
        
        categorical_feature_one_hot = feature_column.indicator_column(categorical_feature)
        feature_columns.append(categorical_feature_one_hot)
    
    # numeric cols
    for header in Numeric_Features:
        feature_columns.append(feature_column.numeric_column(header))
    
    return feature_columns




"""Model"""

def keras_estimator(optimizer):
    """Creates a Logistic Regression model with Keras
        
        Args:
        model_dir: (str) file path where training files will be written.
        config: (tf.estimator.RunConfig) Configuration options to save model.
        Returns:
        A keras.Model
        """
    model = Sequential(feature_layer)
    model.add(Dense(1, input_dim=len(feature_columns), activation='softmax',kernel_regularizer=regularizers.l1_l2(l1=0.0, l2=0.1)))
    #input_shape=(len(feature_columns),) # the input_shape need to be changed
    model.compile(optimizer=optimizer,loss='binary_crossentropy',metrics=["accuracy"])
                    # need to be changed for metrics
                    
    return model



def input_fn(batch_size, mode, TABLE_ID):
    """Input function for training and serving.
        Args:
        batch_size: (int)
        mode: tf.estimator.ModeKeys mode
        Returns:
        A tf.estimator.
    """
    if mode == tf.estimator.ModeKeys.TRAIN:
        ds = read_bigquery(TABLE_ID).shuffle(10000).batch(BATCH_SIZE)
    if mode in (tf.estimator.ModeKeys.EVAL, tf.estimator.ModeKeys.PREDICT):
        ds = read_bigquery(TABLE_ID).batch(BATCH_SIZE)
    return ds # dataset.make_one_shot_iterator().get_next()

def main():
    PROJECT_ID = "amiable-octane-267022"
    TABLE_NAME = "Member_2"
    DATASET_ID = 'census_dataset'
    BATCH_SIZE=32
    training_ds = read_bigquery("Member_2").shuffle(10000).batch(BATCH_SIZE)
    feature_columns = format_features()
    feature_layer = tf.keras.layers.DenseFeatures(feature_columns)
    keras_estimator('sgd').fit(training_ds,epochs=20,verbose=1)


if __name__ == '__main__':
    main()




"""Load Data"""
import os
import pandas
import logging

import tensorflow as tf

from sklearn import model_selection as ms
from sklearn.externals import joblib

from trainer import metadata

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

def over_sample(full_table_path,project_id):
    # read in training data
    df = read_from_bigquery(full_table_path,project_id)
    # Class count
    count_class_0, count_class_1 = df.is_churn.value_counts()
    # Divide by class
    df_class_0 = df[df['is_churn'] == 0]
    df_class_1 = df[df['is_churn'] == 1]
    # Over Sample
    df_class_1_over = df_class_1.sample(round(count_class_0/3), replace=True)
    df_over = pandas.concat([df_class_0, df_class_1_over], axis=0)
    return df_over

def _feature_label_split(data_df, label_column,unused_column):
    """Split the DataFrame into features and label respectively, and remove unused columns
        Args:
        data_df: (pandas.DataFrame) DataFrame the splitting to be performed on
        label_column: (string) name of the label column
        unused_bolumn: (string) name of the unused column
        Returns:
        A Tuple of (pandas.DataFrame, pandas.Series)
        """
    return data_df.loc[:, (data_df.columns != label_column) & (data_df.columns != unused_column)], data_df[label_column]

def dump_object(object_to_dump, output_path):
    """Pickle the object and save to the output_path.

    Args:
      object_to_dump: Python object to be pickled
      output_path: (string) output path which can be Google Cloud Storage

    Returns:
      None
    """

    if not tf.io.gfile.exists(output_path):
        tf.io.gfile.makedirs(os.path.dirname(output_path))
    with tf.io.gfile.GFile(output_path, 'w') as wf:
        joblib.dump(object_to_dump, wf)

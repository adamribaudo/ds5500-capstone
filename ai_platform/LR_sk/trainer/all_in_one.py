"""Load Data"""
import os
import pandas
import logging
from sklearn import linear_model

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/wangzhengye/Desktop/ai_platform/training/LR_sk/amiable-octane-267022-061a6f297eeb.json"

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

def _feature_label_split(data_df, label_column):
    """Split the DataFrame into features and label respectively.
        Args:
        data_df: (pandas.DataFrame) DataFrame the splitting to be performed on
        label_column: (string) name of the label column
        Returns:
        A Tuple of (pandas.DataFrame, pandas.Series)
        """
    return data_df.loc[:, data_df.columns != label_column], data_df[label_column]

def get_estimator(arguments):
    """Generate ML Pipeline which include model training
        
        Args:
        arguments: (argparse.ArgumentParser), parameters passed from command-line
        
        Returns:
        structured.pipeline.Pipeline
        """
    
    # tolerance and C are expected to be passed as
    # command line argument to task.py
    classifier = linear_model.LogisticRegression(
                                                 penalty="l2",
                                                 tol=arguments.tol,
                                                 C = arguments.C
                                                 )
                                                 
    return classifier

def main():
    df = read_from_bigquery("amiable-octane-267022.census_dataset.Member_2","amiable-octane-267022")
    train, label =_feature_label_split(df,"is_churn")
    estimator = get_estimator()
    estimator.fit(train, label)
        #model_output_path = os.path.join(output_dir, 'model',
#       metadata.MODEL_FILE_NAME)



if __name__ == '__main__':
    main()

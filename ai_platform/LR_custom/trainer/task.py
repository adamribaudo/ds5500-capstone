import argparse
import logging
import os
import warnings
from google.cloud import storage


import hypertune
import numpy as np
from datetime import datetime
from sklearn import model_selection, linear_model
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.pipeline import Pipeline, FeatureUnion, make_pipeline
from sklearn.metrics import f1_score, make_scorer,accuracy_score
from trainer import metadata
from trainer import my_module
from trainer import utils

from sklearn.externals import joblib
warnings.filterwarnings('ignore')

def get_estimator(arguments):
    """Generate ML Pipeline which include model training
        
        Args:
        arguments: (argparse.ArgumentParser), parameters passed from command-line
        
        Returns:
        structured.pipeline.Pipeline
        """
    
    numerical_indices = [1, 2, 4, 5,6,7,8,9,10,11,12,13,14]
    categorical_indices = [0]
    original_indices = list(set(range(59))-set(numerical_indices)-set(categorical_indices))
    
    p1 = make_pipeline(my_module.PositionalSelector(categorical_indices),OneHotEncoder())
    p2 = make_pipeline(my_module.PositionalSelector(numerical_indices),StandardScaler())
    p3 = make_pipeline(my_module.PositionalSelector(original_indices))
    
    feats = FeatureUnion([('categoricals', p1),
                          ('numericals', p2),
                          ('originals', p3),])
        
                          # tolerance and C are expected to be passed as
                          # command line argument to task.py
    pipeline = Pipeline([('pre', feats),
                         ('estimator', linear_model.LogisticRegression(penalty="l2",
                                                                       tol=arguments.tol,
                                                                       C = arguments.C,
                                                                       solver='lbfgs',
                                                                       max_iter=10000))])
                          
                          # tolerance and C are expected to be passed as
                          # command line argument to task.py
                          #classifier = linear_model.LogisticRegression(
                          #  penalty="l2",
                          #   tol=arguments.tol,
                          #   C = arguments.C,
                          #   solver='lbfgs',
                          #   max_iter=1000
                          #)
                          
    return pipeline

def _train_and_evaluate(estimator, output_dir):
    """Runs model training and evaluation.

    Args:
      estimator: (pipeline.Pipeline), Pipeline instance, in this case, model training
      dataset: (pandas.DataFrame), DataFrame containing training data
      output_dir: (string), directory that the trained model will be exported

    Returns:
      None
    """
    
    """X_train, y_train =utils._feature_label_split(df_train,"is_churn","msno")
    df_val = utils.read_from_bigquery("amiable-octane-267022.kkbox.output_val_1","amiable-octane-267022")
    X_val, y_val =utils._feature_label_split(df_val,"is_churn","msno")"""
    
    df_train=utils.over_sample("amiable-octane-267022.kkbox.output_train_1","amiable-octane-267022")
    X_train, y_train =utils._feature_label_split(df_train,"is_churn","msno")
    df_val=utils.over_sample("amiable-octane-267022.kkbox.output_val_1","amiable-octane-267022")
    X_val, y_val =utils._feature_label_split(df_val,"is_churn","msno")

    estimator.fit(X_train, y_train)
    f1_scorer = make_scorer(f1_score)
    accuracy_scorer =make_scorer(accuracy_score)

    if metadata.HYPERPARAMTER_TUNING:
        scores=model_selection.cross_val_score(estimator, X_val, y_val, cv=3,scoring=f1_scorer)
        #,scoring=f1_scorer

        logging.info('Score: %s', scores)

        #tune hyper
        hpt = hypertune.HyperTune()
        hpt.report_hyperparameter_tuning_metric(
            hyperparameter_metric_tag='F1_SCORE',
            metric_value=np.mean(scores),
            global_step=10000)
    
#joblib.dump(estimator, 'model.joblib')

    # Write model and eval metrics to `output_dir`
    model_output_path = os.path.join(output_dir, 'model',metadata.MODEL_FILE_NAME)
                
    utils.dump_object(estimator, model_output_path)

def run_experiment(arguments):
    """Testbed for running model training and evaluation."""

    logging.info('Arguments: %s', arguments)

    # Get estimator
    estimator = get_estimator(arguments)
    # my_module.

    # Run training and evaluation
    _train_and_evaluate(estimator, arguments.job_dir)


def _parse_args():
    """Parses command-line arguments."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--log-level',
        help='Logging level.',
        choices=[
            'DEBUG',
            'ERROR',
            'FATAL',
            'INFO',
            'WARN',
        ],
        default='INFO',
    )

    parser.add_argument(
        '--job-dir',
        help='Output directory for exporting model and other metadata.',
        required=True,
    )

    parser.add_argument(
        '--tol',
        help='Tolerance',
        type=float,
        default=1e-4,
    )

    parser.add_argument(
        '--C',
        help='Regularizaiton',
        default=1.0,
        type=float,
    )

    return parser.parse_args()


def main():
    """Entry point"""

    arguments = _parse_args()
    logging.basicConfig(level=arguments.log_level)
    # Run the train and evaluate experiment
    time_start = datetime.utcnow()
    #X_train,y_train,X_val,y_val=get_data()
    run_experiment(arguments)
    time_end = datetime.utcnow()
    time_elapsed = time_end - time_start
    logging.info('Experiment elapsed time: {} seconds'.format(
        time_elapsed.total_seconds()))


if __name__ == '__main__':
    main()

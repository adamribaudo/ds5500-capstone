import argparse
import logging
import os

import hypertune
import numpy as np
from datetime import datetime
from sklearn import model_selection
from trainer import metadata
from trainer import model
from trainer import utils

def _train_and_evaluate(estimator, output_dir):
    """Runs model training and evaluation.

    Args:
      estimator: (pipeline.Pipeline), Pipeline instance, assemble pre-processing
        steps and model training
      dataset: (pandas.DataFrame), DataFrame containing training data
      output_dir: (string), directory that the trained model will be exported

    Returns:
      None
    """
    df_train = utils.read_from_bigquery("amiable-octane-267022.census_dataset.Member_4","amiable-octane-267022")
    X_train, y_train =utils._feature_label_split(df_train,"is_churn")
    df_val = utils.read_from_bigquery("amiable-octane-267022.census_dataset.Member_3","amiable-octane-267022")
    X_val, y_val =utils._feature_label_split(df_val,"is_churn")


    estimator.fit(X_train, y_train)

    # Write model and eval metrics to `output_dir`
    model_output_path = os.path.join(output_dir, 'model',
                                     metadata.MODEL_FILE_NAME)

    utils.dump_object(estimator, model_output_path)

    if metadata.HYPERPARAMTER_TUNING:
        # Note: for now, use `cross_val_score` defaults (i.e. 3-fold)
        scores = model_selection.cross_val_score(estimator, X_val, y_val, cv=3)

        logging.info('Scores: %s', scores)

        # The default name of the metric is training/hptuning/metric.
        # We recommend that you assign a custom name
        # The only functional difference is that if you use a custom name,
        # you must set the hyperparameterMetricTag value in the
        # HyperparameterSpec object in the job request to match your chosen name
        hpt = hypertune.HyperTune()
        hpt.report_hyperparameter_tuning_metric(
            hyperparameter_metric_tag='sk_accuracy',
            metric_value=np.mean(scores),
            global_step=100)


def run_experiment(arguments):
    """Testbed for running model training and evaluation."""
    # Get data for training and evaluation

    logging.info('Arguments: %s', arguments)

    # Get estimator
    estimator = model.get_estimator(arguments)

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
    run_experiment(arguments)
    time_end = datetime.utcnow()
    time_elapsed = time_end - time_start
    logging.info('Experiment elapsed time: {} seconds'.format(
        time_elapsed.total_seconds()))


if __name__ == '__main__':
    main()

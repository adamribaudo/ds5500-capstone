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

"""ML model definitions."""

from sklearn import linear_model

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
        C = arguments.C,
        solver='lbfgs',
        max_iter=1000
    )

    return classifier

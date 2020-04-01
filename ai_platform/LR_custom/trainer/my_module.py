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

from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

# A pipeline to select a subset of features, given their positional indices
class PositionalSelector(BaseEstimator, TransformerMixin):
    def __init__(self, positions):
        self.positions = positions

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return np.array(X)[:, self.positions]

"""
def get_cat(X):
    return X[:,0].reshape(-1,1)

def get_num(X):
    return X[:,[1, 2, 4, 5,6,7,8,9,10,11,12,13,14]]

def get_org(X):
    return X[:,list(set(range(59))-set([1, 2, 4, 5,6,7,8,9,10,11,12,13,14,0]))]
"""


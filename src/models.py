"""Model factories and hyperparameter search spaces.

Every model is a scikit-learn Pipeline, so scaling and column selection are fitted within each
training fold. Labels are integers 0..K-1.
"""

import numpy as np
from scipy.stats import loguniform
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from features import config

TUNED = ("physics_rule", "logistic", "random_forest", "xgboost", "mlp")


class BalancedXGB(ClassifierMixin, BaseEstimator):
    """XGBoost classifier whose class balancing is a tunable setting."""

    def __init__(self, balanced=False, learning_rate=0.1, n_estimators=300, max_depth=6,
                 subsample=1.0, colsample_bytree=1.0, min_child_weight=1, reg_lambda=1.0,
                 random_state=0):
        self.balanced = balanced
        self.learning_rate = learning_rate
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.min_child_weight = min_child_weight
        self.reg_lambda = reg_lambda
        self.random_state = random_state

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        weights = compute_sample_weight("balanced", y) if self.balanced else None
        self.model_ = XGBClassifier(
            objective="multi:softprob", tree_method="hist", eval_metric="mlogloss", n_jobs=1,
            learning_rate=self.learning_rate, n_estimators=self.n_estimators,
            max_depth=self.max_depth, subsample=self.subsample,
            colsample_bytree=self.colsample_bytree, min_child_weight=self.min_child_weight,
            reg_lambda=self.reg_lambda, random_state=self.random_state)
        self.model_.fit(np.asarray(X), y, sample_weight=weights)
        return self

    def predict_proba(self, X):
        return self.model_.predict_proba(np.asarray(X))

    def predict(self, X):
        return self.classes_[np.argmax(self.predict_proba(X), axis=1)]


def make_model(name, seed=0, params=None):
    """Pipeline for one model; `params` are model settings without the 'model__' prefix."""
    cfg = config()
    if name == "majority":
        steps = [("model", DummyClassifier(strategy="most_frequent"))]
    elif name == "physics_rule":
        select = ColumnTransformer([("keep", "passthrough", cfg["physics_rule_features"])])
        steps = [("select", select), ("model", DecisionTreeClassifier(random_state=seed))]
    elif name == "logistic":
        steps = [("scale", StandardScaler()),
                 ("model", LogisticRegression(max_iter=5000, random_state=seed))]
    elif name in ("random_forest", "random_forest_default"):
        steps = [("model", RandomForestClassifier(n_estimators=500, n_jobs=1, random_state=seed))]
    elif name == "xgboost":
        steps = [("model", BalancedXGB(random_state=seed))]
    elif name == "mlp":
        steps = [("scale", StandardScaler()),
                 ("model", MLPClassifier(max_iter=500, early_stopping=True, random_state=seed))]
    else:
        raise ValueError(f"unknown model: {name}")
    pipeline = Pipeline(steps)
    if params:
        pipeline.set_params(**{f"model__{k}": v for k, v in params.items()})
    return pipeline


def search_space(name):
    """Search space with the 'model__' prefix, converted from configs/models.json."""
    space = {}
    for key, values in config()["search_spaces"][name].items():
        if isinstance(values, dict) and "loguniform" in values:
            space[f"model__{key}"] = loguniform(*values["loguniform"])
        elif key == "hidden_layer_sizes":
            space[f"model__{key}"] = [tuple(v) for v in values]
        else:
            space[f"model__{key}"] = list(values)
    return space


def grid_size(space):
    """Number of combinations if every setting is a list, else None (continuous)."""
    size = 1
    for values in space.values():
        if not isinstance(values, list):
            return None
        size *= len(values)
    return size

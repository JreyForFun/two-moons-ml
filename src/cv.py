"""Cross-validation, metrics and paired bootstrap comparisons.

The outer cross-validation gives every training moon one out-of-fold (OOF) prediction from a
model that did not see it. With tune=True, hyperparameters are chosen by randomized search within
each outer training part (nested cross-validation).
"""

import time
import warnings

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score, log_loss,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold

from features import config
from models import grid_size, make_model, search_space

EPS = 1e-15


def run_cv(name, X, y, tune=True, calibrate=False, params=None, seed=None, n_jobs=None):
    """Outer stratified CV. Returns OOF probabilities and per-fold details."""
    cfg = config()
    seed = cfg["seed"] if seed is None else seed
    n_jobs = cfg["n_jobs"] if n_jobs is None else n_jobs
    classes = np.unique(y)
    oof = np.zeros((len(y), len(classes)))
    folds = []
    outer = StratifiedKFold(cfg["outer_folds"], shuffle=True, random_state=seed)
    for k, (train, test) in enumerate(outer.split(X, y)):
        started = time.perf_counter()
        model, best = fit_model(name, X.iloc[train], y[train], tune, seed + k, n_jobs, params)
        if calibrate:
            model = CalibratedClassifierCV(model, method="isotonic", cv=3)
            model.fit(X.iloc[train], y[train])
        oof[test] = model.predict_proba(X.iloc[test])
        folds.append({"fold": k, "test_index": test.tolist(), "best_params": best,
                      "seconds": time.perf_counter() - started,
                      "metrics": metrics(y[test], oof[test])})
    return oof, folds


def fit_model(name, X, y, tune, seed, n_jobs, params=None):
    """Fit one model, tuning it by randomized search when it has a search space."""
    cfg = config()
    pipeline = make_model(name, seed=seed, params=params)
    if not tune or name not in cfg["search_spaces"]:
        return pipeline.fit(X, y), params or {}
    space = search_space(name)
    size = grid_size(space)
    candidates = cfg["search_candidates"] if size is None else min(cfg["search_candidates"], size)
    inner = StratifiedKFold(cfg["inner_folds"], shuffle=True, random_state=seed)
    search = RandomizedSearchCV(pipeline, space, n_iter=candidates, cv=inner,
                                scoring="f1_macro", n_jobs=n_jobs, random_state=seed,
                                refit=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        search.fit(X, y)
    best = {k.removeprefix("model__"): to_json(v) for k, v in search.best_params_.items()}
    return search.best_estimator_, best


def to_json(value):
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def ece(prob, outcome, bins=10):
    """Expected calibration error of a probability for a binary outcome."""
    edges = np.linspace(0, 1, bins + 1)
    index = np.clip(np.digitize(prob, edges) - 1, 0, bins - 1)
    total = 0.0
    for b in range(bins):
        mask = index == b
        if mask.any():
            total += mask.mean() * abs(prob[mask].mean() - outcome[mask].mean())
    return float(total)


def metrics(y, prob, weights=None, survived=0):
    """Classification, probabilistic and binary (survived vs not) metrics."""
    labels = np.arange(prob.shape[1])
    pred = prob.argmax(axis=1)
    clipped = np.clip(prob, EPS, 1)
    clipped = clipped / clipped.sum(axis=1, keepdims=True)
    onehot = np.eye(prob.shape[1])[y]
    alive = (y == survived).astype(int)
    out = {
        "macro_f1": f1_score(y, pred, labels=labels, average="macro", sample_weight=weights,
                             zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y, pred, sample_weight=weights),
        "accuracy": accuracy_score(y, pred, sample_weight=weights),
        "log_loss": log_loss(y, clipped, labels=labels, sample_weight=weights),
        "brier": float(np.average(((prob - onehot) ** 2).sum(axis=1), weights=weights)),
        "recall": recall_score(y, pred, labels=labels, average=None, sample_weight=weights,
                               zero_division=0).tolist(),
        "precision": precision_score(y, pred, labels=labels, average=None,
                                     sample_weight=weights, zero_division=0).tolist(),
        "survived_auc": roc_auc_score(alive, prob[:, survived], sample_weight=weights),
        "survived_accuracy": accuracy_score(alive, (prob[:, survived] >= 0.5).astype(int),
                                            sample_weight=weights),
        "survived_ece": ece(prob[:, survived], alive),
    }
    return {k: (float(v) if not isinstance(v, list) else v) for k, v in out.items()}


def fold_spread(folds, key):
    values = [f["metrics"][key] for f in folds]
    return float(np.mean(values)), float(np.std(values, ddof=1))


def paired_bootstrap(y, prob_a, prob_b, statistic, samples=None, seed=None):
    """Bootstrap distribution of statistic(a) - statistic(b) on the same resampled moons."""
    cfg = config()
    samples = cfg["bootstrap_samples"] if samples is None else samples
    rng = np.random.default_rng(cfg["bootstrap_seed"] if seed is None else seed)
    n = len(y)
    diffs = np.empty(samples)
    for s in range(samples):
        idx = rng.integers(0, n, n)
        diffs[s] = statistic(y[idx], prob_a[idx]) - statistic(y[idx], prob_b[idx])
    return diffs


def interval(values):
    return [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]


def macro_f1(y, prob):
    return f1_score(y, prob.argmax(axis=1), labels=np.arange(prob.shape[1]), average="macro",
                    zero_division=0)


def balanced_accuracy(y, prob):
    return balanced_accuracy_score(y, prob.argmax(axis=1))

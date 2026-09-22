"""
Aura Retail Analytics - Phase 5 Part 1
Machine Learning Models, Cross-Validation & Hyperparameter Tuning Module.
"""

import logging
import os
from typing import Any, Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline

from src.churn.config import (
    CV_FOLDS,
    OUTPUT_MODEL_ARTIFACT,
    RANDOM_SEED,
)

logger = logging.getLogger(__name__)


def get_candidate_models(random_state: int = RANDOM_SEED) -> Dict[str, Any]:
    """
    Instantiate the dictionary of candidate classification models.

    Models:
        - Baseline: DummyClassifier (most frequent class)
        - Logistic Regression (balanced class weights)
        - Random Forest Classifier (balanced class weights, depth controlled)
        - Gradient Boosting Classifier
        - XGBoost Classifier (if xgboost is installed in environment)

    Returns:
        Dict mapping model names to model estimators.
    """
    models = {
        "Baseline (Dummy)": DummyClassifier(strategy="most_frequent"),
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=6,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=random_state,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=random_state,
        ),
    }

    # Dynamically verify XGBoost availability
    try:
        from xgboost import XGBClassifier

        models["XGBoost"] = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=random_state,
            eval_metric="logloss",
        )
    except ImportError:
        logger.warning(
            "XGBoost library not available in environment. "
            "Proceeding with Scikit-Learn candidate models (Logistic Regression, Random Forest, Gradient Boosting)."
        )

    return models


def cross_validate_candidate_models(
    models: Dict[str, Any],
    preprocessor: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv_folds: int = CV_FOLDS,
    random_state: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Perform stratified k-fold cross-validation on the training set for all candidate models.

    Args:
        models: Dict of model instances.
        preprocessor: Configured ColumnTransformer preprocessor.
        X_train: Training features.
        y_train: Training targets.
        cv_folds: Number of stratified folds.
        random_state: Random state for KFold shuffle.

    Returns:
        DataFrame summarizing mean and std for PR-AUC, ROC-AUC, F1, Accuracy, Precision, Recall.
    """
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    results = []

    for name, model in models.items():
        pr_aucs = []
        roc_aucs = []
        f1s = []
        accuracies = []
        precisions = []
        recalls = []

        pipeline = Pipeline(steps=[("prep", preprocessor), ("clf", model)])

        for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

            pipeline.fit(X_tr, y_tr)
            y_pred = pipeline.predict(X_val)

            # Probabilities for curves
            if hasattr(pipeline.named_steps["clf"], "predict_proba"):
                y_prob = pipeline.predict_proba(X_val)[:, 1]
            else:
                y_prob = y_pred.astype(float)

            accuracies.append(accuracy_score(y_val, y_pred))
            precisions.append(precision_score(y_val, y_pred, zero_division=0))
            recalls.append(recall_score(y_val, y_pred, zero_division=0))
            f1s.append(f1_score(y_val, y_pred, zero_division=0))
            roc_aucs.append(roc_auc_score(y_val, y_prob))
            pr_aucs.append(average_precision_score(y_val, y_prob))

        results.append(
            {
                "Model": name,
                "CV_PR_AUC_Mean": np.mean(pr_aucs),
                "CV_PR_AUC_Std": np.std(pr_aucs),
                "CV_ROC_AUC_Mean": np.mean(roc_aucs),
                "CV_ROC_AUC_Std": np.std(roc_aucs),
                "CV_F1_Mean": np.mean(f1s),
                "CV_F1_Std": np.std(f1s),
                "CV_Accuracy_Mean": np.mean(accuracies),
                "CV_Precision_Mean": np.mean(precisions),
                "CV_Recall_Mean": np.mean(recalls),
            }
        )

    return pd.DataFrame(results)


def tune_candidate_model(
    model_name: str,
    preprocessor: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    cv_folds: int = CV_FOLDS,
    random_state: int = RANDOM_SEED,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Perform a controlled hyperparameter grid search on the training folds.

    Args:
        model_name: Name of model to tune ('Random Forest', 'Gradient Boosting', or 'Logistic Regression').
        preprocessor: ColumnTransformer.
        X_train: Training feature DataFrame.
        y_train: Training target Series.
        cv_folds: Number of stratified folds.
        random_state: Random state for deterministic tuning.

    Returns:
        Tuple of (best_fitted_pipeline, best_params_dict).
    """
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

    if model_name == "Random Forest":
        base_model = RandomForestClassifier(class_weight="balanced", random_state=random_state)
        param_grid = {
            "clf__n_estimators": [100, 150],
            "clf__max_depth": [4, 6],
            "clf__min_samples_leaf": [5, 10],
        }
    elif model_name == "Gradient Boosting":
        base_model = GradientBoostingClassifier(random_state=random_state)
        param_grid = {
            "clf__n_estimators": [100, 150],
            "clf__max_depth": [3, 4],
            "clf__learning_rate": [0.05, 0.08],
        }
    elif model_name == "XGBoost":
        from xgboost import XGBClassifier

        base_model = XGBClassifier(eval_metric="logloss", random_state=random_state)
        param_grid = {
            "clf__n_estimators": [100, 150],
            "clf__max_depth": [3, 4],
            "clf__learning_rate": [0.05, 0.08],
        }
    else:  # Logistic Regression
        base_model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state)
        param_grid = {
            "clf__C": [0.1, 1.0, 10.0],
        }

    pipeline = Pipeline(steps=[("prep", preprocessor), ("clf", base_model)])

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring="average_precision",  # PR-AUC optimization
        cv=skf,
        n_jobs=-1,
        refit=True,
    )

    grid_search.fit(X_train, y_train)

    return grid_search.best_estimator_, grid_search.best_params_


def save_model(
    model_pipeline: Pipeline,
    filepath: Optional[str] = None,
) -> str:
    """
    Serialize the trained pipeline artifact to disk.

    Args:
        model_pipeline: Fitted Scikit-Learn Pipeline.
        filepath: Target output file path.

    Returns:
        Absolute path to saved model file.
    """
    if filepath is None:
        filepath = OUTPUT_MODEL_ARTIFACT

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model_pipeline, filepath)
    return filepath


def load_model(filepath: Optional[str] = None) -> Pipeline:
    """
    Load a serialized model pipeline artifact from disk.

    Args:
        filepath: Target file path.

    Returns:
        Loaded Pipeline.
    """
    if filepath is None:
        filepath = OUTPUT_MODEL_ARTIFACT

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model artifact not found at: {filepath}")

    return joblib.load(filepath)

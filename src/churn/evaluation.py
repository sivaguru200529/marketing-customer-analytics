"""
Aura Retail Analytics - Phase 5 Part 1
Model Evaluation, Metric Calculation & Comparison Module.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.churn.config import PRIMARY_SELECTION_METRIC


def evaluate_model(
    pipeline: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
) -> Dict[str, Any]:
    """
    Evaluate a fitted pipeline on the untouched held-out test set.

    Computes:
        Accuracy, Precision, Recall, F1-Score, ROC-AUC, PR-AUC, Confusion Matrix.

    Args:
        pipeline: Fitted model pipeline.
        X_test: Held-out test features.
        y_test: Held-out test target.
        model_name: Name of model for reporting.

    Returns:
        Dict containing all scalar metrics, confusion matrix values, and probabilities.
    """
    y_pred = pipeline.predict(X_test)

    # Probabilities
    if hasattr(pipeline.named_steps["clf"], "predict_proba"):
        y_prob = pipeline.predict_proba(X_test)[:, 1]
    else:
        y_prob = y_pred.astype(float)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))

    cm = confusion_matrix(y_test, y_pred)
    # Binary classification layout: tn, fp, fn, tp
    tn, fp, fn, tp = cm.ravel()

    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    return {
        "Model": model_name,
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1": f1,
        "ROC-AUC": roc_auc,
        "PR-AUC": pr_auc,
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
        "y_pred": y_pred,
        "y_prob": y_prob,
        "confusion_matrix": cm,
        "classification_report": report_dict,
    }


def compare_models(eval_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Assemble the formal model comparison table from evaluation result dicts.

    Columns:
        Model, Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC

    Args:
        eval_results: List of evaluation dicts from evaluate_model().

    Returns:
        DataFrame sorted descending by PRIMARY_SELECTION_METRIC (PR-AUC).
    """
    rows = []
    for res in eval_results:
        rows.append(
            {
                "Model": res["Model"],
                "Accuracy": round(res["Accuracy"], 4),
                "Precision": round(res["Precision"], 4),
                "Recall": round(res["Recall"], 4),
                "F1": round(res["F1"], 4),
                "ROC-AUC": round(res["ROC-AUC"], 4),
                "PR-AUC": round(res["PR-AUC"], 4),
            }
        )

    df_comp = pd.DataFrame(rows)
    df_comp = df_comp.sort_values(by=PRIMARY_SELECTION_METRIC, ascending=False).reset_index(drop=True)
    return df_comp


def select_best_model(
    comparison_df: pd.DataFrame,
    metric: str = PRIMARY_SELECTION_METRIC,
) -> Tuple[str, float]:
    """
    Deterministically select the winning model based on the configured selection criterion.

    Args:
        comparison_df: DataFrame from compare_models().
        metric: Column name to maximize (default 'PR-AUC').

    Returns:
        Tuple of (selected_model_name, best_metric_score).
    """
    if metric not in comparison_df.columns:
        raise KeyError(f"Selection metric '{metric}' not found in comparison table columns.")

    # Exclude baseline dummy from winning if any real model outperforms it
    non_dummy = comparison_df[~comparison_df["Model"].str.contains("Dummy", case=False)]
    candidates = non_dummy if len(non_dummy) > 0 else comparison_df

    best_row = candidates.sort_values(by=metric, ascending=False).iloc[0]
    selected_name = str(best_row["Model"])
    best_score = float(best_row[metric])

    return selected_name, best_score


def generate_confusion_matrix_dataframe(eval_result: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a clean, exportable DataFrame of the confusion matrix.
    """
    cm = eval_result["confusion_matrix"]
    cm_df = pd.DataFrame(
        cm,
        index=["Actual_Retained (0)", "Actual_Churned (1)"],
        columns=["Predicted_Retained (0)", "Predicted_Churned (1)"],
    )
    return cm_df

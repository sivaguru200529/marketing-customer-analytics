"""
Aura Retail Analytics - Phase 5 Part 1
CLI Entry Point & Orchestrator for Churn Prediction & Model Evaluation.

Usage:
    python -m src.churn.run_churn
"""

import logging
import os
import sys
import time
from typing import Dict

from src.churn.config import (
    CATEGORICAL_FEATURE_COLUMNS,
    DEFAULT_CUSTOMER_INTELLIGENCE_CSV,
    DEFAULT_FIGURES_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    DEFAULT_SUMMARIES_DIR,
    FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    OUTPUT_CHURN_PREDICTIONS,
    OUTPUT_CONFUSION_MATRIX,
    OUTPUT_CV_RESULTS,
    OUTPUT_FEATURE_IMPORTANCE,
    OUTPUT_MODEL_ARTIFACT,
    OUTPUT_MODEL_COMPARISON,
    OUTPUT_PREDICTION_SUMMARY,
    OUTPUT_TARGET_SUMMARY,
    PRIMARY_SELECTION_METRIC,
    RANDOM_SEED,
    TEST_SIZE,
)
from src.churn.evaluation import (
    compare_models,
    evaluate_model,
    generate_confusion_matrix_dataframe,
    select_best_model,
)
from src.churn.explainability import extract_feature_importance
from src.churn.features import prepare_feature_dataset, verify_leakage_controls
from src.churn.loader import load_customer_intelligence_data
from src.churn.models import (
    cross_validate_candidate_models,
    get_candidate_models,
    save_model,
)
from src.churn.prediction import (
    generate_customer_predictions,
    generate_prediction_summary,
)
from src.churn.preprocessing import build_preprocessor, split_data
from src.churn.report import generate_all_visualizations, generate_churn_prediction_report
from src.churn.target import create_churn_target, generate_target_summary, validate_target
from sklearn.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("src.churn.run_churn")


def run_churn_pipeline() -> int:
    """Execute the end-to-end churn prediction and model evaluation pipeline."""
    start_time = time.time()
    print("================================================================================")
    print("AURA RETAIL ANALYTICS — PHASE 5 PART 1: CHURN PREDICTION & MODEL EVALUATION")
    print("================================================================================")

    # 1. Ingest Input Dataset
    print("\n[1/14] Ingesting authoritative Customer Intelligence dataset...")
    df_raw = load_customer_intelligence_data(DEFAULT_CUSTOMER_INTELLIGENCE_CSV)
    print(f"  -> Ingested Dataset: {len(df_raw):,} rows x {df_raw.shape[1]} columns")

    # 2. Formulate Behavioral Proxy Churn Target
    print("\n[2/14] Defining behavioral proxy churn target (inactivity > 90d & tenure >= 120d)...")
    df_with_target = create_churn_target(df_raw)
    _, target_stats = validate_target(df_with_target)
    print(f"  -> Total Customers:       {target_stats['total_customers']:,}")
    print(f"  -> Proxy Churned (1):     {target_stats['churned_customers']:,} ({target_stats['churn_rate'] * 100:.2f}%)")
    print(f"  -> Retained (0):          {target_stats['non_churned_customers']:,} ({target_stats['non_churn_rate'] * 100:.2f}%)")
    if target_stats["warnings"]:
        for w in target_stats["warnings"]:
            print(f"     [WARNING] {w}")

    # 3. Assemble Feature Matrix & Verify Leakage Isolation
    print("\n[3/14] Assembling feature matrix and strictly quarantining leakage variables...")
    verify_leakage_controls(FEATURE_COLUMNS)
    X, y, customer_ids = prepare_feature_dataset(df_with_target)
    print(f"  -> Predictor Matrix (X):  {X.shape[0]:,} rows x {X.shape[1]} features")
    print(f"  -> Target Vector (y):     {len(y):,} rows (Class balance: {y.mean():.4f})")
    print(f"  -> Leakage Quarantined:   'tenure_days' strictly excluded + 14 recency/cluster fields quarantined")

    # 4. Partition Data into Train / Test Splits
    print("\n[4/14] Performing stratified 80/20 train/test split (seed = 42)...")
    X_train, X_test, y_train, y_test = split_data(
        X=X,
        y=y,
        test_size=TEST_SIZE,
        random_state=RANDOM_SEED,
        stratify=True,
    )
    print(f"  -> Training Split:        {len(X_train):,} rows ({len(X_train)/len(X)*100:.0f}%)")
    print(f"  -> Test Split (Holdout):  {len(X_test):,} rows ({len(X_test)/len(X)*100:.0f}%)")

    # 5. Build Preprocessor Pipeline
    print("\n[5/14] Building ColumnTransformer preprocessor (median impute, standard scale, OHE)...")
    preprocessor = build_preprocessor(
        numeric_cols=NUMERIC_FEATURE_COLUMNS,
        categorical_cols=CATEGORICAL_FEATURE_COLUMNS,
    )

    # 6. Instantiate Candidate Models
    print("\n[6/14] Initializing candidate classification models...")
    candidate_models = get_candidate_models(random_state=RANDOM_SEED)
    for model_name in candidate_models.keys():
        print(f"  -> Registered: {model_name}")

    # 7. Stratified 5-Fold Cross-Validation on Training Split
    print("\n[7/14] Executing stratified 5-fold cross-validation on training split...")
    cv_results_df = cross_validate_candidate_models(
        models=candidate_models,
        preprocessor=preprocessor,
        X_train=X_train,
        y_train=y_train,
        cv_folds=5,
        random_state=RANDOM_SEED,
    )
    for _, row in cv_results_df.iterrows():
        print(f"  -> {row['Model']:<22} | CV PR-AUC: {row['CV_PR_AUC_Mean']:.4f} ± {row['CV_PR_AUC_Std']:.4f} | CV ROC-AUC: {row['CV_ROC_AUC_Mean']:.4f}")

    # 8. Train & Evaluate on Pristine Holdout Test Set
    print("\n[8/14] Evaluating all models on untouched 20% holdout test set...")
    eval_results = []
    fitted_pipelines: Dict[str, Pipeline] = {}

    for name, model in candidate_models.items():
        pipe = Pipeline(steps=[("prep", preprocessor), ("clf", model)])
        pipe.fit(X_train, y_train)
        fitted_pipelines[name] = pipe

        eval_res = evaluate_model(pipeline=pipe, X_test=X_test, y_test=y_test, model_name=name)
        eval_results.append(eval_res)

    comparison_df = compare_models(eval_results)
    print("\n  --- TEST SET PERFORMANCE COMPARISON ---")
    print(comparison_df.to_string(index=False))

    # 9. Deterministic Champion Model Selection
    print(f"\n[9/14] Selecting champion model via predefined criterion ({PRIMARY_SELECTION_METRIC})...")
    best_model_name, best_score = select_best_model(comparison_df, metric=PRIMARY_SELECTION_METRIC)
    best_eval = next(r for r in eval_results if r["Model"] == best_model_name)
    best_pipeline = fitted_pipelines[best_model_name]
    print(f"  -> Champion Model:        {best_model_name}")
    print(f"  -> Measured {PRIMARY_SELECTION_METRIC}:     {best_score:.4f}")
    print(f"  -> Test ROC-AUC:          {best_eval['ROC-AUC']:.4f}")
    print(f"  -> Test F1-Score:         {best_eval['F1']:.4f}")

    # 10. Persist Champion Pipeline Artifact
    print("\n[10/14] Persisting champion model pipeline artifact...")
    saved_path = save_model(best_pipeline, OUTPUT_MODEL_ARTIFACT)
    print(f"  -> Saved Model Artifact:  {saved_path}")

    # 11. Customer-Level Predictions & Descriptive Risk Bands
    print("\n[11/14] Generating customer-level predictions & descriptive risk bands...")
    df_predictions = generate_customer_predictions(
        fitted_pipeline=best_pipeline,
        X_full=X,
        customer_ids=customer_ids,
    )
    pred_summary_df = generate_prediction_summary(df_predictions)
    print(f"  -> Scored Customers:      {len(df_predictions):,} (100% unique IDs)")
    print(f"  -> Predicted Churn Count: {int(df_predictions['predicted_churn'].sum()):,} ({float(df_predictions['predicted_churn'].mean()) * 100:.2f}%)")
    for _, r in pred_summary_df.iterrows():
        print(f"     * {r['Churn Risk Band']:<12}: {r['Customer Count']:,} ({r['Customer Share (%)']}%) | Mean Prob: {r['Mean Probability']:.4f}")

    # 12. Model Explainability & Feature Importances
    print("\n[12/14] Extracting feature importances & non-causal explainability...")
    df_importance = extract_feature_importance(
        fitted_pipeline=best_pipeline,
        numeric_cols=NUMERIC_FEATURE_COLUMNS,
        categorical_cols=CATEGORICAL_FEATURE_COLUMNS,
    )
    print("  -> Top 5 Behavioral Predictors:")
    for idx, r in df_importance.head(5).iterrows():
        print(f"     {idx+1}. {r['feature']:<25} (Importance: {r['importance']:.4f}, Share: {r['relative_importance_pct']}%)")

    # 13. Render Visualizations
    print("\n[13/14] Rendering 6 publication-grade Matplotlib visualizations...")
    chart_paths = generate_all_visualizations(
        df_with_target=df_with_target,
        eval_results=eval_results,
        y_test=y_test,
        best_model_name=best_model_name,
        df_importance=df_importance,
        df_predictions=df_predictions,
        output_dir=DEFAULT_FIGURES_DIR,
    )
    for name, path in chart_paths.items():
        print(f"  -> Chart [{name}]: {path}")

    # 14. Export Summaries & Documentation Report
    print("\n[14/14] Exporting analytical summaries & compiling 24-section report...")
    os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEFAULT_SUMMARIES_DIR, exist_ok=True)

    target_summary_df = generate_target_summary(df_with_target)
    cm_df = generate_confusion_matrix_dataframe(best_eval)

    df_predictions.to_csv(OUTPUT_CHURN_PREDICTIONS, index=False)
    comparison_df.to_csv(OUTPUT_MODEL_COMPARISON, index=False)
    df_importance.to_csv(OUTPUT_FEATURE_IMPORTANCE, index=False)
    target_summary_df.to_csv(OUTPUT_TARGET_SUMMARY, index=False)
    pred_summary_df.to_csv(OUTPUT_PREDICTION_SUMMARY, index=False)
    cv_results_df.to_csv(OUTPUT_CV_RESULTS, index=False)
    cm_df.to_csv(OUTPUT_CONFUSION_MATRIX, index=True)

    report_file = generate_churn_prediction_report(
        df_with_target=df_with_target,
        target_summary_df=target_summary_df,
        comparison_df=comparison_df,
        cv_results_df=cv_results_df,
        best_model_name=best_model_name,
        best_eval_dict=best_eval,
        df_importance=df_importance,
        prediction_summary_df=pred_summary_df,
        df_predictions=df_predictions,
        report_path=DEFAULT_REPORT_PATH,
    )
    print(f"  -> Compiled Report:       {report_file}")

    elapsed = time.time() - start_time
    print("\n================================================================================")
    print(f"PHASE 5 PART 1 COMPLETED SUCCESSFULLY IN {elapsed:.2f}s")
    print(f"Champion Model: {best_model_name} | {PRIMARY_SELECTION_METRIC}: {best_score:.4f} | ROC-AUC: {best_eval['ROC-AUC']:.4f}")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_churn_pipeline())

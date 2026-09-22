"""
Aura Retail Analytics - Phase 5 Part 1 Test Suite
Automated Verification for Behavioral Churn Prediction & Model Evaluation Pipeline.
"""

import os
import numpy as np
import pandas as pd
import pytest

from src.churn.config import (
    CATEGORICAL_FEATURE_COLUMNS,
    CHURN_RECENCY_THRESHOLD_DAYS,
    CHURN_RISK_BAND_HIGH,
    CHURN_RISK_BAND_LOW,
    CHURN_TENURE_THRESHOLD_DAYS,
    DEFAULT_CUSTOMER_INTELLIGENCE_CSV,
    DEFAULT_FIGURES_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PATH,
    DEFAULT_SUMMARIES_DIR,
    FEATURE_COLUMNS,
    ID_COLUMNS,
    LEAKAGE_COLUMNS,
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
    REFERENCE_CHURN_RATE,
    REFERENCE_CHURNED_COUNT,
    REFERENCE_CUSTOMER_COUNT,
    REFERENCE_RETAINED_COUNT,
    TARGET_COLUMNS,
    TEST_SIZE,
)
from src.churn.evaluation import (
    compare_models,
    evaluate_model,
    generate_confusion_matrix_dataframe,
    select_best_model,
)
from src.churn.explainability import CAUSATION_DISCLAIMER, extract_feature_importance
from src.churn.features import prepare_feature_dataset, verify_leakage_controls
from src.churn.loader import load_customer_intelligence_data
from src.churn.models import (
    cross_validate_candidate_models,
    get_candidate_models,
    load_model,
    save_model,
)
from src.churn.prediction import (
    generate_customer_predictions,
    generate_prediction_summary,
)
from src.churn.preprocessing import (
    build_preprocessor,
    get_transformed_feature_names,
    split_data,
)
from src.churn.target import create_churn_target, generate_target_summary, validate_target
from sklearn.pipeline import Pipeline


@pytest.fixture(scope="module")
def df_source():
    """Load authoritative customer intelligence dataset."""
    assert os.path.exists(DEFAULT_CUSTOMER_INTELLIGENCE_CSV), "customer_intelligence.csv missing!"
    return load_customer_intelligence_data(DEFAULT_CUSTOMER_INTELLIGENCE_CSV)


@pytest.fixture(scope="module")
def df_target(df_source):
    """Generate dataframe with behavioral proxy churn target."""
    return create_churn_target(df_source)


@pytest.fixture(scope="module")
def feature_data(df_target):
    """Assemble feature matrix, target, and IDs."""
    return prepare_feature_dataset(df_target)


# ==============================================================================
# 1. Input Dataset Integrity
# ==============================================================================

def test_source_dataset_exists_and_valid(df_source):
    """Verify source dataset exists and has exactly 10,000 rows."""
    assert len(df_source) == REFERENCE_CUSTOMER_COUNT
    assert df_source.shape[1] >= 40


def test_customer_id_unique_and_non_null(df_source):
    """Verify customer_id is 100% unique primary key."""
    assert "customer_id" in df_source.columns
    assert df_source["customer_id"].nunique() == REFERENCE_CUSTOMER_COUNT
    assert not df_source["customer_id"].duplicated().any()
    assert not df_source["customer_id"].isna().any()


# ==============================================================================
# 2. Behavioral Proxy Churn Target Formulation & Validation
# ==============================================================================

def test_target_generation_binary_values(df_target):
    """Verify target column exists and contains strictly binary {0, 1} values."""
    assert "is_churned" in df_target.columns
    unique_vals = set(df_target["is_churned"].unique())
    assert unique_vals.issubset({0, 1})
    assert len(unique_vals) == 2


def test_target_contains_no_nulls(df_target):
    """Verify target column contains zero null values."""
    assert df_target["is_churned"].notna().all()


def test_target_matches_threshold_logic(df_target):
    """Verify target strictly obeys (recency > threshold) & (tenure >= threshold)."""
    expected = (
        (df_target["recency_days"] > CHURN_RECENCY_THRESHOLD_DAYS)
        & (df_target["tenure_days"] >= CHURN_TENURE_THRESHOLD_DAYS)
    ).astype(int)
    assert (df_target["is_churned"] == expected).all()


def test_target_validation_returns_accurate_stats(df_target):
    """Verify validate_target correctly computes customer counts and rates."""
    valid, stats = validate_target(df_target)
    assert valid is True
    assert stats["total_customers"] == REFERENCE_CUSTOMER_COUNT
    assert stats["churned_customers"] == REFERENCE_CHURNED_COUNT
    assert stats["non_churned_customers"] == REFERENCE_RETAINED_COUNT
    assert np.isclose(stats["churn_rate"], REFERENCE_CHURN_RATE, atol=1e-3)


def test_target_summary_dataframe_structure(df_target):
    """Verify target summary table is properly formed."""
    df_sum = generate_target_summary(df_target)
    assert len(df_sum) >= 8
    assert "metric" in df_sum.columns and "value" in df_sum.columns


# ==============================================================================
# 3. Strict Data Leakage Prevention & Tenure Quarantine
# ==============================================================================

def test_tenure_days_strictly_excluded_from_features():
    """CRITICAL: Verify tenure_days is NOT in FEATURE_COLUMNS."""
    assert "tenure_days" not in FEATURE_COLUMNS, "CRITICAL: tenure_days must be quarantined!"
    assert "tenure_days" in LEAKAGE_COLUMNS


def test_leakage_columns_strictly_excluded():
    """Verify none of the defined leakage columns enter FEATURE_COLUMNS."""
    overlap = set(FEATURE_COLUMNS).intersection(set(LEAKAGE_COLUMNS))
    assert len(overlap) == 0, f"Leakage detected in feature columns: {overlap}"


def test_customer_identifiers_excluded_from_features():
    """Verify customer ID, name, email are excluded from FEATURE_COLUMNS."""
    overlap = set(FEATURE_COLUMNS).intersection(set(ID_COLUMNS))
    assert len(overlap) == 0, f"Customer identifiers detected in feature columns: {overlap}"


def test_target_excluded_from_features():
    """Verify target column is excluded from FEATURE_COLUMNS."""
    assert "is_churned" not in FEATURE_COLUMNS


def test_verify_leakage_controls_raises_on_violation():
    """Verify verify_leakage_controls raises ValueError on leaky columns."""
    with pytest.raises(ValueError, match="CRITICAL DATA LEAKAGE VIOLATION"):
        verify_leakage_controls(["total_orders", "tenure_days"])

    with pytest.raises(ValueError, match="CRITICAL DATA LEAKAGE"):
        verify_leakage_controls(["total_orders", "recency_days"])

    with pytest.raises(ValueError, match="IDENTIFIER LEAKAGE"):
        verify_leakage_controls(["total_orders", "customer_id"])


def test_feature_matrix_dimensions_and_finite_values(feature_data):
    """Verify feature matrix X has correct shape, no infinite values, and matching grain."""
    X, y, customer_ids = feature_data
    assert len(X) == REFERENCE_CUSTOMER_COUNT
    assert len(y) == REFERENCE_CUSTOMER_COUNT
    assert len(customer_ids) == REFERENCE_CUSTOMER_COUNT
    assert list(X.columns) == FEATURE_COLUMNS
    for col in NUMERIC_FEATURE_COLUMNS:
        assert not np.isinf(X[col]).any()


# ==============================================================================
# 4. Preprocessing & Data Splitting
# ==============================================================================

def test_train_test_split_shapes_and_stratification(feature_data):
    """Verify 80/20 train/test split preserves class balance."""
    X, y, _ = feature_data
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED)

    assert len(X_train) == int(REFERENCE_CUSTOMER_COUNT * (1 - TEST_SIZE))
    assert len(X_test) == int(REFERENCE_CUSTOMER_COUNT * TEST_SIZE)
    assert np.isclose(y_train.mean(), y.mean(), atol=0.01)
    assert np.isclose(y_test.mean(), y.mean(), atol=0.01)


def test_preprocessor_fits_and_imputes_missing_values(feature_data):
    """Verify preprocessor handles missing delivered_aov and scales features."""
    X, y, _ = feature_data
    preprocessor = build_preprocessor(NUMERIC_FEATURE_COLUMNS, CATEGORICAL_FEATURE_COLUMNS)
    X_trans = preprocessor.fit_transform(X)

    # Check finite transformed output
    assert not np.isnan(X_trans).any(), "Transformed feature matrix contains NaNs!"
    assert not np.isinf(X_trans).any(), "Transformed feature matrix contains Infs!"

    # Check feature name extraction
    names = get_transformed_feature_names(preprocessor, NUMERIC_FEATURE_COLUMNS, CATEGORICAL_FEATURE_COLUMNS)
    assert len(names) == X_trans.shape[1]
    assert len(names) > len(NUMERIC_FEATURE_COLUMNS)


# ==============================================================================
# 5. Candidate Models, Evaluation & Deterministic Selection
# ==============================================================================

def test_candidate_models_instantiation():
    """Verify baseline and core ML models are present."""
    models = get_candidate_models(random_state=RANDOM_SEED)
    assert "Baseline (Dummy)" in models
    assert "Logistic Regression" in models
    assert "Random Forest" in models
    assert "Gradient Boosting" in models


def test_model_training_and_evaluation(feature_data):
    """Verify training pipeline fits on train set and evaluates on holdout test set."""
    X, y, _ = feature_data
    X_train, X_test, y_train, y_test = split_data(X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED)
    preprocessor = build_preprocessor()

    models = get_candidate_models(random_state=RANDOM_SEED)
    eval_results = []

    for name, model in models.items():
        pipe = Pipeline(steps=[("prep", preprocessor), ("clf", model)])
        pipe.fit(X_train, y_train)
        res = evaluate_model(pipe, X_test, y_test, model_name=name)
        eval_results.append(res)

        # Check metric ranges
        assert 0.0 <= res["Accuracy"] <= 1.0
        assert 0.0 <= res["Precision"] <= 1.0
        assert 0.0 <= res["Recall"] <= 1.0
        assert 0.0 <= res["F1"] <= 1.0
        assert 0.0 <= res["ROC-AUC"] <= 1.0
        assert 0.0 <= res["PR-AUC"] <= 1.0
        assert res["TN"] + res["FP"] + res["FN"] + res["TP"] == len(X_test)

    # Model comparison table
    df_comp = compare_models(eval_results)
    assert len(df_comp) == len(models)
    assert list(df_comp.columns) == ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"]

    # Deterministic selection based on PR-AUC
    best_name, best_score = select_best_model(df_comp, metric=PRIMARY_SELECTION_METRIC)
    assert best_name != "Baseline (Dummy)"
    assert best_score > 0.50


def test_model_artifact_save_and_load(tmp_path, feature_data):
    """Verify model serialization and deserialization via joblib."""
    X, y, _ = feature_data
    # Sample balanced subset with both classes
    X_sample = pd.concat([X[y == 0].iloc[:100], X[y == 1].iloc[:100]])
    y_sample = pd.concat([y[y == 0].iloc[:100], y[y == 1].iloc[:100]])

    preprocessor = build_preprocessor()
    models = get_candidate_models(random_state=RANDOM_SEED)
    pipe = Pipeline(steps=[("prep", preprocessor), ("clf", models["Logistic Regression"])])
    pipe.fit(X_sample, y_sample)

    tmp_file = str(tmp_path / "test_model.joblib")
    saved_path = save_model(pipe, tmp_file)
    assert os.path.exists(saved_path)

    loaded_pipe = load_model(saved_path)
    preds_orig = pipe.predict_proba(X.iloc[:50])
    preds_loaded = loaded_pipe.predict_proba(X.iloc[:50])
    np.testing.assert_allclose(preds_orig, preds_loaded)


# ==============================================================================
# 6. Customer-Level Predictions & Risk Bands
# ==============================================================================

def test_customer_predictions_integrity(feature_data):
    """Verify predictions schema, row counts, probabilities, and risk bands."""
    X, y, customer_ids = feature_data
    X_sample = pd.concat([X[y == 0].iloc[:200], X[y == 1].iloc[:200]])
    y_sample = pd.concat([y[y == 0].iloc[:200], y[y == 1].iloc[:200]])

    preprocessor = build_preprocessor()
    models = get_candidate_models(random_state=RANDOM_SEED)
    pipe = Pipeline(steps=[("prep", preprocessor), ("clf", models["Logistic Regression"])])
    pipe.fit(X_sample, y_sample)

    df_preds = generate_customer_predictions(pipe, X, customer_ids)

    assert len(df_preds) == REFERENCE_CUSTOMER_COUNT
    assert df_preds["customer_id"].nunique() == REFERENCE_CUSTOMER_COUNT
    assert not df_preds["customer_id"].duplicated().any()
    assert not df_preds["churn_probability"].isna().any()
    assert ((df_preds["churn_probability"] >= 0.0) & (df_preds["churn_probability"] <= 1.0)).all()
    assert set(df_preds["predicted_churn"].unique()).issubset({0, 1})
    assert set(df_preds["churn_risk_band"].unique()).issubset({"Low Risk", "Medium Risk", "High Risk"})

    # Check summary
    df_sum = generate_prediction_summary(df_preds)
    assert len(df_sum) == 3
    assert df_sum["Customer Count"].sum() == REFERENCE_CUSTOMER_COUNT


def test_part2_fields_strictly_absent_from_predictions(feature_data):
    """CRITICAL: Ensure Phase 5 Part 2 business prioritization fields are absent."""
    X, y, customer_ids = feature_data
    X_sample = pd.concat([X[y == 0].iloc[:100], X[y == 1].iloc[:100]])
    y_sample = pd.concat([y[y == 0].iloc[:100], y[y == 1].iloc[:100]])

    preprocessor = build_preprocessor()
    models = get_candidate_models(random_state=RANDOM_SEED)
    pipe = Pipeline(steps=[("prep", preprocessor), ("clf", models["Logistic Regression"])])
    pipe.fit(X_sample, y_sample)

    df_preds = generate_customer_predictions(pipe, X, customer_ids)

    prohibited_fields = [
        "priority_score",
        "recommended_campaign",
        "recommended_action",
        "campaign_priority",
        "action_recommendation",
        "marketing_offer",
        "customer_action",
    ]
    for field in prohibited_fields:
        assert field not in df_preds.columns, f"Prohibited Part 2 field '{field}' detected in predictions!"


# ==============================================================================
# 7. Explainability & Non-Causal Notice
# ==============================================================================

def test_feature_importance_extraction_and_disclaimer(feature_data):
    """Verify feature importances are ranked and include non-causal disclaimer."""
    X, y, _ = feature_data
    X_sample = pd.concat([X[y == 0].iloc[:150], X[y == 1].iloc[:150]])
    y_sample = pd.concat([y[y == 0].iloc[:150], y[y == 1].iloc[:150]])

    preprocessor = build_preprocessor()
    models = get_candidate_models(random_state=RANDOM_SEED)
    pipe = Pipeline(steps=[("prep", preprocessor), ("clf", models["Random Forest"])])
    pipe.fit(X_sample, y_sample)

    df_imp = extract_feature_importance(pipe, NUMERIC_FEATURE_COLUMNS, CATEGORICAL_FEATURE_COLUMNS)

    assert "feature" in df_imp.columns
    assert "importance" in df_imp.columns
    assert "relative_importance_pct" in df_imp.columns
    assert len(df_imp) > 20
    assert (df_imp["importance"] >= 0.0).all()
    assert "causal" in CAUSATION_DISCLAIMER.lower()


# ==============================================================================
# 8. Output Files & Artifact Verification
# ==============================================================================

def test_pipeline_output_artifacts_exist():
    """Verify that all Phase 5 Part 1 output files exist and are non-empty."""
    required_files = [
        OUTPUT_CHURN_PREDICTIONS,
        OUTPUT_MODEL_COMPARISON,
        OUTPUT_FEATURE_IMPORTANCE,
        OUTPUT_TARGET_SUMMARY,
        OUTPUT_PREDICTION_SUMMARY,
        OUTPUT_CV_RESULTS,
        OUTPUT_CONFUSION_MATRIX,
        OUTPUT_MODEL_ARTIFACT,
        DEFAULT_REPORT_PATH,
        os.path.join(DEFAULT_FIGURES_DIR, "target_distribution.png"),
        os.path.join(DEFAULT_FIGURES_DIR, "roc_curves.png"),
        os.path.join(DEFAULT_FIGURES_DIR, "precision_recall_curves.png"),
        os.path.join(DEFAULT_FIGURES_DIR, "confusion_matrix.png"),
        os.path.join(DEFAULT_FIGURES_DIR, "feature_importance.png"),
        os.path.join(DEFAULT_FIGURES_DIR, "probability_distribution.png"),
    ]

    for filepath in required_files:
        assert os.path.exists(filepath), f"Expected artifact missing: {filepath}"
        assert os.path.getsize(filepath) > 50, f"Expected artifact unexpectedly small/empty: {filepath}"

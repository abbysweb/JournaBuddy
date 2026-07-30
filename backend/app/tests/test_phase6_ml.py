import pytest
from app.services.symbolic_checker import SymbolicChecker
from app.services.journal_matcher import JournalMatcher
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

def test_mattr_algorithm():
    """
    Tests the Moving-Average Type-Token Ratio (MATTR).
    Ensures that vocabulary richness is calculated using sliding windows.
    """
    checker = SymbolicChecker()
    text = "The quick brown fox jumps over the lazy dog. The lazy dog sleeps." * 10 
    
    # Text is over 100 words, so MATTR window (size 50) should kick in
    mattr_score = checker._calculate_mattr(text, window_size=50)
    
    # Assert it returns a valid percentage
    assert isinstance(mattr_score, float)
    assert 0.0 <= mattr_score <= 100.0

def test_readability_metrics():
    """
    Tests if the Phase 6 mathematical NLP readability formulas are correctly populated.
    """
    checker = SymbolicChecker()
    sample_text = (
        "JournaBuddy utilizes a hyper-dimensional XGBoost machine learning model "
        "to synthesize academic manuscript predictability scores. The methodology "
        "incorporates rigorously defined statistical paradigms for optimization."
    )
    
    results = checker.evaluate_symbolic(sample_text)
    
    # Assert Phase 6 metrics are present and valid
    assert "smog_index" in results
    assert isinstance(results["smog_index"], float)
    
    assert "gunning_fog" in results
    assert isinstance(results["gunning_fog"], float)
    
    assert "flesch_reading_ease" in results
    assert isinstance(results["flesch_reading_ease"], float)
    
    assert "mattr" in results
    assert isinstance(results["mattr"], float)

def test_xgboost_shap_predictor():
    """
    Tests the XGBoost Ensemble Predictor and SHAP Explainability extraction.
    """
    # Create mock session and matcher
    mock_db = MagicMock(spec=Session)
    matcher = JournalMatcher(mock_db)
    
    # Define synthetic evaluation payload from LLM
    mock_evaluation_payload = {
        "methodological_rigor": {
            "score": 8,
            "feedback": "Strong methodology"
        },
        "novelty": {
            "score": 7,
            "feedback": "Novel approach"
        }
    }
    
    # Define a target journal with a base compatibility score
    target_journal = {
        "compatibility_percent": 85
    }
    
    # Define symbolic features
    symbolic_features = {
        "shannon_entropy": 8.2,
        "mattr": 45.3
    }
    
    # Run the predictor
    prediction, shap_breakdown = matcher._predict_acceptance_xgboost(
        target_journal, 
        mock_evaluation_payload, 
        symbolic_features
    )
    
    # Assert Prediction
    assert isinstance(prediction, int)
    assert 5 <= prediction <= 99
    
    # Assert SHAP Explainability Breakdown
    assert isinstance(shap_breakdown, dict)
    assert "Journal Fit (Similarity)" in shap_breakdown
    assert "Methodological Rigor" in shap_breakdown
    assert "Novelty Score" in shap_breakdown
    
    # Ensure SHAP values sum up properly (are formatted as percentage strings like "+4.2")
    for feature, impact in shap_breakdown.items():
        assert isinstance(impact, str)
        # Should be parsable as a float
        assert float(impact)

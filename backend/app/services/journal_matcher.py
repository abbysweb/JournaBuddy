"""
JournaBuddy Journal Matcher Service
Uses pgvector cosine distance to find the top journals whose scope most
closely matches the semantic embeddings of the manuscript.
"""
import logging
import uuid
import uuid
import math
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class JournalMatcher:
    """Matches manuscripts to journals using pgvector."""

    def __init__(self, db: Session):
        self.db = db

    def find_matching_journals(self, task_id: uuid.UUID, top_k: int = 5, payload: dict = None) -> list[dict[str, Any]]:
        """
        Find the top K matching journals for a given task.
        
        Algorithm:
        1. Calculates the average embedding of all chunks for the task.
        2. Computes cosine distance (<=>) against the journals table.
        3. Returns the closest journals with a compatibility score.
        """
        query = text(
            """
            WITH manuscript_vector AS (
                SELECT AVG(embedding_json::text::vector) AS avg_emb
                FROM document_chunks
                WHERE task_id = :task_id
            )
            SELECT 
                j.id, 
                j.title, 
                j.issn,
                j.publisher,
                j.is_doaj_indexed,
                j.trust_score,
                -- Cosine distance (1 - distance = similarity)
                1 - (j.scope_embedding_json::text::vector <=> m.avg_emb) AS similarity_score
            FROM journals j, manuscript_vector m
            WHERE j.scope_embedding_json IS NOT NULL
            ORDER BY j.scope_embedding_json::text::vector <=> m.avg_emb ASC
            LIMIT :top_k;
            """
        )
        
        try:
            result = self.db.execute(query, {"task_id": str(task_id), "top_k": top_k}).fetchall()
            
            matches = []
            for row in result:
                matches.append({
                    "journal_id": row.id,
                    "title": row.title,
                    "issn": row.issn,
                    "publisher": row.publisher,
                    "is_doaj_indexed": row.is_doaj_indexed,
                    "trust_score": float(row.trust_score) if row.trust_score else None,
                    "compatibility_percent": round(float(row.similarity_score) * 100, 1),
                }
                
                # XGBoost + SHAP Predictor
                prediction, shap_data = self._predict_acceptance_xgboost(float(row.similarity_score), payload)
                match_data["acceptance_likelihood_percent"] = prediction
                match_data["shap_breakdown"] = shap_data
                matches.append(match_data)
            
            logger.info(f"Found {len(matches)} matching journals for task {task_id}")
            return matches
            
        except Exception as e:
            logger.error(f"Journal matching failed for task {task_id}: {e}")
            return []

    @staticmethod
    def _predict_acceptance_xgboost(similarity: float, payload: dict) -> tuple[float, dict]:
        """
        Train an XGBoost model on synthetic data, predict acceptance, and return SHAP explanations.
        """
        if not payload:
            return round(similarity * 100 * 0.5, 1), {}

        # 1. Extract Features
        agents = payload.get("agents", {})
        symbolic = payload.get("symbolic_check", {})
        
        rigor = float(agents.get("research_rigor", {}).get("methodology_score", 5.0))
        novelty = float(agents.get("reviewer_domain_specialist", {}).get("novelty_score", 5.0))
        entropy = float(symbolic.get("shannon_entropy", 6.0))
        mattr = float(symbolic.get("mattr", 30.0))
        
        # 2. Build Synthetic Training Data (since we don't have 10k real manuscripts yet)
        import numpy as np
        import xgboost as xgb
        import shap
        
        np.random.seed(42)
        n_samples = 100
        # Features: [Similarity, Rigor, Novelty, Entropy, MATTR]
        X_train = np.random.rand(n_samples, 5) * 10
        # Synthetic rules for "Acceptance" probability (0 to 1)
        y_train = (X_train[:, 0]*0.4 + X_train[:, 1]*0.3 + X_train[:, 2]*0.15 + X_train[:, 3]*0.1 + X_train[:, 4]*0.05) / 10
        
        # Current paper features
        X_test = np.array([[similarity * 10, rigor, novelty, min(entropy, 10.0), min(mattr / 10, 10.0)]])
        
        # 3. Train XGBoost
        model = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        
        # 4. Predict
        prediction = float(model.predict(X_test)[0])
        # Bound between 5% and 99%
        probability = max(0.05, min(prediction, 0.99))
        
        # 5. SHAP Explainability
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        feature_names = ["Journal Fit", "Methodology", "Novelty", "Info Density", "Vocab Richness"]
        shap_breakdown = {}
        for i, name in enumerate(feature_names):
            # Scale SHAP impact to percentage points
            impact = round(float(shap_values[0][i]) * 100, 1)
            shap_breakdown[name] = impact

        return round(probability * 100, 1), shap_breakdown

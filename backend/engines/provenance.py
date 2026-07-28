import json
import time
from database import SessionLocal, ProvenanceLog

class ProvenanceEngine:
    @staticmethod
    def log(task_id: str, metric_name: str, metric_value: any, formula: str, data_sources: list[str], confidence_level: str, explanation: str, raw_data_snapshot: any = None) -> int:
        """
        Logs a single calculation with all metadata needed for the truthfulness/provenance layer.
        Returns the ID of the newly created log entry.
        """
        db = SessionLocal()
        try:
            log_entry = ProvenanceLog(
                task_id=task_id,
                metric_name=metric_name,
                metric_value=json.dumps(metric_value),
                formula=formula,
                data_sources=json.dumps(data_sources),
                confidence_level=confidence_level,
                timestamp=time.time(),
                raw_data_snapshot=json.dumps(raw_data_snapshot) if raw_data_snapshot is not None else None,
                explanation=explanation
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry.id
        except Exception as e:
            print(f"[ProvenanceEngine] Error logging provenance for {metric_name}: {e}")
            return -1
        finally:
            db.close()

    @staticmethod
    def get(provenance_id: int) -> dict | None:
        """Retrieves a provenance log by ID."""
        db = SessionLocal()
        try:
            entry = db.query(ProvenanceLog).filter(ProvenanceLog.id == provenance_id).first()
            if entry:
                return {
                    "id": entry.id,
                    "task_id": entry.task_id,
                    "metric_name": entry.metric_name,
                    "metric_value": json.loads(entry.metric_value) if entry.metric_value else None,
                    "formula": entry.formula,
                    "data_sources": json.loads(entry.data_sources) if entry.data_sources else [],
                    "confidence_level": entry.confidence_level,
                    "timestamp": entry.timestamp,
                    "raw_data_snapshot": json.loads(entry.raw_data_snapshot) if entry.raw_data_snapshot else None,
                    "explanation": entry.explanation
                }
            return None
        except Exception as e:
            print(f"[ProvenanceEngine] Error getting provenance {provenance_id}: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_by_task(task_id: str) -> list[dict]:
        """Retrieves all provenance logs associated with a specific task."""
        db = SessionLocal()
        try:
            entries = db.query(ProvenanceLog).filter(ProvenanceLog.task_id == task_id).all()
            results = []
            for entry in entries:
                results.append({
                    "id": entry.id,
                    "task_id": entry.task_id,
                    "metric_name": entry.metric_name,
                    "metric_value": json.loads(entry.metric_value) if entry.metric_value else None,
                    "formula": entry.formula,
                    "data_sources": json.loads(entry.data_sources) if entry.data_sources else [],
                    "confidence_level": entry.confidence_level,
                    "timestamp": entry.timestamp,
                    "raw_data_snapshot": json.loads(entry.raw_data_snapshot) if entry.raw_data_snapshot else None,
                    "explanation": entry.explanation
                })
            return results
        except Exception as e:
            print(f"[ProvenanceEngine] Error listing provenance for task {task_id}: {e}")
            return []
        finally:
            db.close()

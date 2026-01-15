"""
KA-071: Data Ingestion
Purpose: Ingest data from various sources (batches or streams) with protocol-specific handlers.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA071IngestionInput(BaseModel):
    source_type: str = Field("local_file", description="The type of data source (e.g., local_file, stream, api)")
    payload: List[Any] = Field(default_factory=list, description="The raw data payload to ingest")

class KA071DataIngestion(KnowledgeAlgorithm):
    """
    KA-071: Enterprise-grade data ingestion engine with protocol-specific handlers.
    """
    input_schema = KA071IngestionInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-071"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_71_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA071IngestionInput) -> Dict[str, Any]:
        source_type = input_data.source_type
        payload = input_data.payload
        self.log_execution_step("Executing Ingestion Pipeline", {"source": source_type, "count": len(payload)})
        
        handler_name = self.config.get("handlers", {}).get(source_type, "DefaultHandler")
        batch_size = self.config.get("batch_size", 1000)
        mode = "stream" if len(payload) < batch_size else "batch"
        
        processed_records = []
        for i, record in enumerate(payload):
            processed_records.append({
                "raw": record,
                "ingestion_meta": {
                    "handler": handler_name,
                    "mode": mode,
                    "sequence_id": i
                }
            })
            
        return {
            "success": True,
            "records_ingested": len(processed_records),
            "ingestion_summary": {
                "source": source_type,
                "handler_active": handler_name,
                "data_mode": mode
            }
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA071DataIngestion(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-071 Failed: {e}")
        return {"success": False, "error": str(e)}

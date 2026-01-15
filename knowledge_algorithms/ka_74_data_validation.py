"""
KA-074: Data Validation
Purpose: Validate records against integrity constraints, data types, and business rules.
"""
import logging
import json
import os
import re
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA074DataValidation(KnowledgeAlgorithm):
    """
    KA-074: Data integrity and constraint validation engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_74_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        records = input_data.get("records", [])
        
        self.log_execution_step("Validating Integrity Constraints", {"record_count": len(records)})
        
        rules = self.config.get("validation_rules", [])
        valid_records = []
        invalid_records = []
        
        for record in records:
            errors = []
            if not isinstance(record, dict):
                errors.append("Record is not a dictionary")
            else:
                for rule in rules:
                    field = rule.get("field")
                    constraint = rule.get("constraint")
                    val = record.get(field)
                    
                    if constraint == "required" and val is None:
                        errors.append(f"Missing required field: {field}")
                    elif constraint == "range" and val is not None:
                        if not (rule.get("min", 0) <= val <= rule.get("max", 1)):
                            errors.append(f"Field {field} value {val} out of range")
                    elif constraint == "regex" and val is not None:
                        if not re.match(rule.get("pattern", ".*"), str(val)):
                            errors.append(f"Field {field} failed regex validation")
            
            if errors:
                invalid_records.append({"record": record, "errors": errors})
            else:
                valid_records.append(record)
                
        return {
            "ka_id": "KA-074",
            "ka_name": "Data Validation",
            "success": True,
            "validation_summary": {
                "total": len(records),
                "valid": len(valid_records),
                "invalid": len(invalid_records)
            },
            "quarantined": invalid_records if self.config.get("quarantine_invalid_records", True) else []
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA074DataValidation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-074 Failed: {e}")
        return {"success": False, "error": str(e)}

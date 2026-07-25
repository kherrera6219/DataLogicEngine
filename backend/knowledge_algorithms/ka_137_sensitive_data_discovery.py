"""KA-137: bounded sensitive-data discovery without value disclosure."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

PATTERNS = {
    "email": re.compile(
        r"(?<![\w.+-])[\w.+-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,63}"
        r"(?![A-Za-z0-9_-])"
    ),
    "ssn": re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    "phone": re.compile(r"(?<!\d)(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}(?!\d)"),
    "api_key": re.compile(r"(?i)\b(?:api[_-]?key|token)[=: ]+[A-Za-z0-9_-]{16,128}\b"),
}


class DiscoveryDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(min_length=1, max_length=200)
    text: str = Field(max_length=1_000_000)


class KA137Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "documents": [
                        {
                            "document_id": "document-1",
                            "text": "Contact owner@example.com.",
                        }
                    ],
                    "detect_types": ["email"],
                }
            ]
        },
    )

    documents: list[DiscoveryDocument] = Field(min_length=1, max_length=1_000)
    detect_types: list[Literal["email", "ssn", "phone", "api_key"]] = Field(
        default=["email", "ssn", "phone", "api_key"], min_length=1
    )


class KA137SensitiveDataDiscovery(KnowledgeAlgorithm):
    """Return type and location metadata while excluding matched values."""

    input_schema = KA137Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-137"

    def _run_logic(self, input_data: KA137Input) -> dict[str, Any]:
        findings = []
        for document in sorted(input_data.documents, key=lambda row: row.document_id):
            for data_type in sorted(set(input_data.detect_types)):
                for match in PATTERNS[data_type].finditer(document.text):
                    findings.append(
                        {
                            "document_id": document.document_id,
                            "data_type": data_type,
                            "start": match.start(),
                            "end": match.end(),
                            "matched_length": match.end() - match.start(),
                        }
                    )
        findings.sort(
            key=lambda row: (row["document_id"], row["start"], row["data_type"])
        )
        return {
            "success": True,
            "status": "sensitive_data_discovered",
            "findings": findings,
            "matched_values_returned": False,
            "documents_modified": 0,
            "deterministic": True,
            "limitations": (
                "Pattern matching can produce false positives and negatives; "
                "discovery is distinct from privacy filtering or classification."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA137SensitiveDataDiscovery(context).run(context)

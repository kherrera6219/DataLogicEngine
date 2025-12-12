"""
Data classification and labeling system for enterprise security.

This module implements:
- Data sensitivity classification (Public, Internal, Confidential, Restricted)
- PII (Personally Identifiable Information) detection and labeling
- Automatic data handling policy enforcement
- Compliance with GDPR, CCPA, HIPAA requirements
- Audit logging for classified data access

Compliance: SOC 2 Type 2, ISO 27001, GDPR, CCPA, HIPAA
"""

from enum import Enum
from typing import Dict, Any, List, Set, Optional
from datetime import datetime, timedelta
import re
import hashlib


class DataClassification(Enum):
    """Data sensitivity classification levels."""

    PUBLIC = "public"  # Public information, no restrictions
    INTERNAL = "internal"  # Internal use only, not for public distribution
    CONFIDENTIAL = "confidential"  # Sensitive business information
    RESTRICTED = "restricted"  # Highly sensitive, strictly controlled (PII, PHI, financial)

    @property
    def priority(self) -> int:
        """Classification priority for handling conflicts."""
        priorities = {
            DataClassification.PUBLIC: 0,
            DataClassification.INTERNAL: 1,
            DataClassification.CONFIDENTIAL: 2,
            DataClassification.RESTRICTED: 3
        }
        return priorities[self]

    @property
    def retention_days(self) -> Optional[int]:
        """Default retention period in days."""
        retention = {
            DataClassification.PUBLIC: None,  # No automatic deletion
            DataClassification.INTERNAL: 2555,  # 7 years
            DataClassification.CONFIDENTIAL: 2555,  # 7 years
            DataClassification.RESTRICTED: 2555  # 7 years (compliance requirement)
        }
        return retention[self]

    @property
    def requires_encryption(self) -> bool:
        """Whether data requires encryption at rest."""
        return self in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]

    @property
    def requires_audit(self) -> bool:
        """Whether access requires audit logging."""
        return self in [DataClassification.CONFIDENTIAL, DataClassification.RESTRICTED]


class PIIType(Enum):
    """Types of Personally Identifiable Information."""

    # Direct identifiers
    SSN = "ssn"  # Social Security Number
    PASSPORT = "passport"  # Passport number
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"

    # Contact information
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"

    # Financial information
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    TAX_ID = "tax_id"

    # Biometric
    FINGERPRINT = "fingerprint"
    FACIAL_RECOGNITION = "facial_recognition"
    BIOMETRIC = "biometric"

    # Health information (PHI)
    MEDICAL_RECORD = "medical_record"
    HEALTH_INSURANCE = "health_insurance"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"

    # Personal details
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    DEVICE_ID = "device_id"
    GEOLOCATION = "geolocation"


class DataClassifier:
    """
    Data classification and PII detection system.

    Automatically classifies data and detects PII for compliance.
    """

    # Regex patterns for PII detection
    PII_PATTERNS = {
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
        PIIType.CREDIT_CARD: r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        PIIType.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }

    # Field names that indicate PII
    PII_FIELD_NAMES = {
        PIIType.SSN: ['ssn', 'social_security', 'social_security_number'],
        PIIType.EMAIL: ['email', 'email_address', 'user_email'],
        PIIType.PHONE: ['phone', 'phone_number', 'mobile', 'telephone'],
        PIIType.ADDRESS: ['address', 'street', 'street_address', 'home_address'],
        PIIType.CREDIT_CARD: ['credit_card', 'card_number', 'cc_number'],
        PIIType.NAME: ['name', 'full_name', 'first_name', 'last_name', 'username'],
        PIIType.DATE_OF_BIRTH: ['dob', 'date_of_birth', 'birth_date', 'birthdate'],
        PIIType.PASSPORT: ['passport', 'passport_number'],
        PIIType.DRIVERS_LICENSE: ['drivers_license', 'license_number', 'dl_number'],
        PIIType.MEDICAL_RECORD: ['medical_record', 'mrn', 'patient_id'],
        PIIType.TAX_ID: ['tax_id', 'ein', 'tin'],
    }

    def __init__(self, audit_logger=None):
        """Initialize data classifier."""
        self.audit_logger = audit_logger
        self.classification_cache = {}

    def detect_pii(self, data: str, field_name: Optional[str] = None) -> List[PIIType]:
        """
        Detect PII types in data.

        Args:
            data: String data to analyze
            field_name: Optional field name for context

        Returns:
            List of detected PII types
        """
        if not data:
            return []

        detected_pii = []

        # Check field name first
        if field_name:
            field_lower = field_name.lower()
            for pii_type, field_names in self.PII_FIELD_NAMES.items():
                if any(fn in field_lower for fn in field_names):
                    detected_pii.append(pii_type)

        # Pattern matching
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, str(data)):
                if pii_type not in detected_pii:
                    detected_pii.append(pii_type)

        if detected_pii:
            self._log_audit("pii_detected", {
                "field_name": field_name,
                "pii_types": [pii.value for pii in detected_pii],
                "data_hash": hashlib.sha256(str(data).encode()).hexdigest()[:16]
            })

        return detected_pii

    def classify_field(self, field_name: str, field_value: Any = None) -> DataClassification:
        """
        Classify a field based on name and optionally value.

        Args:
            field_name: Name of the field
            field_value: Optional value for deeper analysis

        Returns:
            DataClassification level
        """
        field_lower = field_name.lower()

        # Restricted - PII and highly sensitive data
        restricted_keywords = [
            'ssn', 'social_security', 'passport', 'credit_card', 'bank_account',
            'password', 'secret', 'private_key', 'api_key', 'token',
            'medical', 'health', 'diagnosis', 'prescription',
            'biometric', 'fingerprint', 'facial'
        ]
        if any(keyword in field_lower for keyword in restricted_keywords):
            return DataClassification.RESTRICTED

        # Check for PII in value
        if field_value:
            pii_detected = self.detect_pii(str(field_value), field_name)
            if pii_detected:
                return DataClassification.RESTRICTED

        # Confidential - Business sensitive
        confidential_keywords = [
            'salary', 'compensation', 'revenue', 'profit', 'cost',
            'contract', 'agreement', 'pricing', 'strategy',
            'internal', 'confidential', 'proprietary'
        ]
        if any(keyword in field_lower for keyword in confidential_keywords):
            return DataClassification.CONFIDENTIAL

        # Internal - General business data
        internal_keywords = [
            'employee', 'department', 'team', 'project',
            'customer', 'order', 'invoice', 'ticket'
        ]
        if any(keyword in field_lower for keyword in internal_keywords):
            return DataClassification.INTERNAL

        # Default to Internal for safety
        return DataClassification.INTERNAL

    def classify_dict(self, data: Dict[str, Any]) -> Dict[str, DataClassification]:
        """
        Classify all fields in a dictionary.

        Args:
            data: Dictionary to classify

        Returns:
            Dictionary mapping field names to classifications
        """
        classifications = {}

        for field_name, field_value in data.items():
            classifications[field_name] = self.classify_field(field_name, field_value)

        # Overall classification is the highest level found
        overall_classification = max(
            classifications.values(),
            key=lambda c: c.priority
        )

        self._log_audit("data_classified", {
            "field_count": len(data),
            "overall_classification": overall_classification.value,
            "classifications": {k: v.value for k, v in classifications.items()}
        })

        return classifications

    def get_data_label(self, classification: DataClassification) -> Dict[str, Any]:
        """
        Get data handling label for classification level.

        Returns metadata and requirements for handling data.
        """
        return {
            "classification": classification.value,
            "priority": classification.priority,
            "requires_encryption": classification.requires_encryption,
            "requires_audit": classification.requires_audit,
            "retention_days": classification.retention_days,
            "handling_instructions": self._get_handling_instructions(classification),
            "compliance_frameworks": self._get_compliance_frameworks(classification)
        }

    def _get_handling_instructions(self, classification: DataClassification) -> List[str]:
        """Get handling instructions for classification level."""
        instructions = {
            DataClassification.PUBLIC: [
                "No special handling required",
                "May be freely distributed"
            ],
            DataClassification.INTERNAL: [
                "For internal use only",
                "Do not share externally without approval",
                "Store in secure internal systems"
            ],
            DataClassification.CONFIDENTIAL: [
                "Restricted to authorized personnel",
                "Encrypt during transmission",
                "Store in encrypted databases",
                "Log all access",
                "Do not share via email without encryption"
            ],
            DataClassification.RESTRICTED: [
                "Highly restricted access",
                "Encryption required at rest and in transit",
                "Comprehensive audit logging mandatory",
                "Multi-factor authentication required",
                "Data minimization principles apply",
                "Secure deletion required when no longer needed",
                "Cannot be shared without explicit authorization"
            ]
        }
        return instructions.get(classification, [])

    def _get_compliance_frameworks(self, classification: DataClassification) -> List[str]:
        """Get applicable compliance frameworks."""
        frameworks = {
            DataClassification.PUBLIC: [],
            DataClassification.INTERNAL: ["ISO 27001"],
            DataClassification.CONFIDENTIAL: ["SOC 2 Type 2", "ISO 27001"],
            DataClassification.RESTRICTED: [
                "SOC 2 Type 2",
                "ISO 27001",
                "GDPR",
                "CCPA",
                "HIPAA",
                "PCI DSS"
            ]
        }
        return frameworks.get(classification, [])

    def should_encrypt(self, field_name: str, field_value: Any = None) -> bool:
        """Determine if field should be encrypted."""
        classification = self.classify_field(field_name, field_value)
        return classification.requires_encryption

    def should_audit(self, field_name: str, field_value: Any = None) -> bool:
        """Determine if field access should be audited."""
        classification = self.classify_field(field_name, field_value)
        return classification.requires_audit

    def get_retention_policy(self, classification: DataClassification) -> Dict[str, Any]:
        """
        Get data retention policy for classification level.

        Returns:
            Dictionary with retention policy details
        """
        return {
            "classification": classification.value,
            "retention_days": classification.retention_days,
            "deletion_method": "secure" if classification.requires_encryption else "standard",
            "archive_required": classification in [
                DataClassification.CONFIDENTIAL,
                DataClassification.RESTRICTED
            ],
            "backup_retention_days": 90,  # Standard backup retention
            "legal_hold_support": True
        }

    def mask_pii(self, data: str, pii_types: Optional[List[PIIType]] = None) -> str:
        """
        Mask PII in data for display purposes.

        Args:
            data: String containing potential PII
            pii_types: Optional list of specific PII types to mask

        Returns:
            Masked string
        """
        if not data:
            return data

        masked = data

        # Auto-detect if not specified
        if pii_types is None:
            pii_types = self.detect_pii(data)

        # Apply masking patterns
        for pii_type in pii_types:
            if pii_type == PIIType.SSN:
                masked = re.sub(r'\b(\d{3})-(\d{2})-(\d{4})\b', r'***-**-\3', masked)
            elif pii_type == PIIType.CREDIT_CARD:
                masked = re.sub(
                    r'\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b',
                    r'****-****-****-\4',
                    masked
                )
            elif pii_type == PIIType.EMAIL:
                masked = re.sub(
                    r'\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
                    r'\1***@\2',
                    masked
                )
            elif pii_type == PIIType.PHONE:
                masked = re.sub(
                    r'\b(\+?\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b',
                    r'***-***-\3',
                    masked
                )

        return masked

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Log classification operation to audit log."""
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type=event_type,
                details=details,
                severity="INFO"
            )


# Singleton instance
_data_classifier_instance: Optional[DataClassifier] = None


def get_data_classifier(audit_logger=None) -> DataClassifier:
    """Get or create singleton data classifier instance."""
    global _data_classifier_instance
    if _data_classifier_instance is None:
        _data_classifier_instance = DataClassifier(audit_logger=audit_logger)
    return _data_classifier_instance

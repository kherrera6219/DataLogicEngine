import unittest
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.schemas.request_schemas import StorageTestRequest, AudioSynthesizeRequest
from pydantic import ValidationError

class TestRequestSchemas(unittest.TestCase):
    def test_storage_test_request_valid(self):
        """Verify valid storage test request passes."""
        data = {
            "service": "postgres",
            "host": "localhost",
            "port": 5432
        }
        req = StorageTestRequest(**data)
        self.assertEqual(req.service, "postgres")

    def test_storage_test_request_invalid_service(self):
        """Verify invalid service is rejected."""
        data = {"service": "malicious_service"}
        with self.assertRaises(ValidationError):
            StorageTestRequest(**data)

    def test_path_traversal_detection(self):
        """Verify path traversal is caught by validator."""
        data = {
            "service": "vector",
            "local_path": "../../etc/passwd"
        }
        with self.assertRaises(ValidationError):
            StorageTestRequest(**data)

    def test_audio_request_limits(self):
        """Verify text length limits in audio request."""
        # Too short
        with self.assertRaises(ValidationError):
            AudioSynthesizeRequest(text="")
        
        # Too long
        with self.assertRaises(ValidationError):
            AudioSynthesizeRequest(text="a" * 5001)

if __name__ == "__main__":
    unittest.main()

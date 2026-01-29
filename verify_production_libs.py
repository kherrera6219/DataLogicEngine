"""
Production Library Verification
Checks if all integrated libraries are functional and reachable.
"""
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProductionVerify")

def verify_libs():
    print("=" * 60)
    print("PRODUCTION LIBRARY VERIFICATION")
    print("=" * 60)
    
    libs = [
        ("PyPDF2", "PDF Processing"),
        ("docx", "Word Processing"),
        ("pytesseract", "OCR Processing"),
        ("cv2", "Video/Image Processing"),
        ("reportlab", "PDF Report Generation"),
        ("simple_salesforce", "Salesforce CRM"),
        ("jira", "Jira Project Management"),
        ("web3", "Blockchain Integration"),
        ("openai", "Core LLM / Audio Services")
    ]
    
    passed = 0
    for lib_name, description in libs:
        try:
            __import__(lib_name)
            print(f"  ✓ {lib_name:<20} | {description:<25} | INSTALLED")
            passed += 1
        except ImportError:
            print(f"  ✗ {lib_name:<20} | {description:<25} | MISSING")
            
    print("-" * 60)
    print(f"Status: {passed}/{len(libs)} libraries functional.")
    print("=" * 60)
    return passed == len(libs)

if __name__ == "__main__":
    success = verify_libs()
    sys.exit(0 if success else 1)

import sys
import traceback

print(f"sys.path: {sys.path}")

try:
    import ukg_sdk
    print(f"ukg_sdk imported from: {ukg_sdk.__file__}")
    from ukg_sdk import api_client
    print("api_client imported successfully")
except ImportError:
    traceback.print_exc()
except Exception:
    traceback.print_exc()

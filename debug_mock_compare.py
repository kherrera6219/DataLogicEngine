
from unittest.mock import MagicMock
from datetime import datetime

m = MagicMock()
try:
    print(m >= datetime.now())
except Exception as e:
    print(f"Error: {e}")

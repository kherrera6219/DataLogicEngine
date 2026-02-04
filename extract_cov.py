import json
import os

coverage_file = 'backend/coverage.json'
if os.path.exists(coverage_file):
    with open(coverage_file, 'r') as f:
        data = json.load(f)
        total = data.get('totals', {})
        percent = total.get('percent_covered_display', 'N/A')
        print(f"TOTAL_COVERAGE={percent}")
else:
    print("Coverage file not found")

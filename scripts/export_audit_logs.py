#!/usr/bin/env python3
"""
Audit Log Export Tool

Export UKG audit logs to CSV for compliance and SIEM integration.
Usage:
    python export_audit_logs.py --output compliance_report.csv --days 30
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.security.audit_logger import AuditLogger

def main():
    parser = argparse.ArgumentParser(description='Export Audit Logs to CSV')
    parser.add_argument('--output', '-o', default='audit_export.csv', help='Output CSV file path')
    parser.add_argument('--days', '-d', type=int, default=7, help='Number of days to export (default: 7)')
    parser.add_argument('--start', '-s', help='Start date (YYYY-MM-DD), overrides --days')
    parser.add_argument('--end', '-e', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Determine date range
    end_date = datetime.now()
    if args.end:
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        # Set to end of day
        end_date = end_date.replace(hour=23, minute=59, second=59)
        
    start_date = end_date - timedelta(days=args.days)
    if args.start:
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        
    print(f"Exporting audit logs from {start_date.date()} to {end_date.date()}...")
    
    logger = AuditLogger()
    try:
        count = logger.export_to_csv(args.output, start_time=start_date, end_time=end_date)
        print(f"Successfully exported {count} records to {args.output}")
        sys.exit(0)
    except Exception as e:
        print(f"Error exporting logs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

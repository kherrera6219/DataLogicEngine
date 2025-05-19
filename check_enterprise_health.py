
#!/usr/bin/env python3
"""
UKG Enterprise Health Checker

This script checks the health of all UKG enterprise services and reports their status.
"""

import requests
import sys
import os
import json
import argparse
from datetime import datetime
from tabulate import tabulate

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.config_manager import get_config
    config = get_config()
except ImportError:
    print("Error: Cannot import config manager. Make sure backend/config_manager.py exists.")
    sys.exit(1)

def check_service_health(service_name):
    """Check the health of a service by name"""
    try:
        health_url = config.get_health_check_url(service_name)
        response = requests.get(health_url, timeout=2)
        if response.status_code == 200:
            return True, response.json() if response.headers.get('content-type') == 'application/json' else {}
        else:
            return False, {"status_code": response.status_code}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def check_all_services():
    """Check the health of all services"""
    results = []
    
    # Check core services
    services = ["api_gateway", "webhook_server", "model_context", "core_ukg"]
    if not config.get("system.debug"):
        services.append("frontend")  # Only in production
        
    for service_name in services:
        healthy, data = check_service_health(service_name)
        port = config.get_port(service_name)
        status = "HEALTHY" if healthy else "DOWN"
        
        results.append({
            "service": service_name,
            "port": port,
            "status": status,
            "health_url": config.get_health_check_url(service_name),
            "data": data
        })
    
    return results

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Check health of UKG Enterprise services")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()
    
    results = check_all_services()
    
    if args.json:
        # JSON output
        print(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "services": results
        }, indent=2))
    else:
        # Tabular output
        table_data = []
        for result in results:
            table_data.append([
                result["service"],
                result["port"],
                result["status"],
                result["health_url"]
            ])
        
        print("\nUKG Enterprise Services Health Check")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(tabulate(table_data, headers=["Service", "Port", "Status", "Health URL"], tablefmt="grid"))
        
        # Show overall status
        all_healthy = all(result["status"] == "HEALTHY" for result in results)
        print(f"\nOverall Status: {'HEALTHY' if all_healthy else 'DEGRADED'}")
        
        if not all_healthy:
            print("\nDown Services:")
            for result in results:
                if result["status"] != "HEALTHY":
                    print(f"  - {result['service']} (Port {result['port']})")

if __name__ == "__main__":
    main()

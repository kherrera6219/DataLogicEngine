#!/usr/bin/env python
"""
Security Scanning Script for DataLogicEngine

Runs automated security scans using:
- Bandit: Python code static analysis (finds security issues)
- Safety: Dependency vulnerability scanning (checks for CVEs)

Usage:
    python run_security_scan.py              # Run all scans
    python run_security_scan.py --bandit     # Only run Bandit
    python run_security_scan.py --safety     # Only run Safety
    python run_security_scan.py --ci         # CI mode (fail on errors)
"""

import sys
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path


class SecurityScanner:
    """Automated security scanning orchestrator"""

    def __init__(self, ci_mode=False):
        """
        Initialize security scanner.

        Args:
            ci_mode: If True, exit with error code on failures
        """
        self.ci_mode = ci_mode
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'bandit': None,
            'safety': None,
            'overall_status': 'unknown'
        }

    def show_banner(self):
        """Display scan banner"""
        print("=" * 70)
        print("DataLogicEngine - Security Scan")
        print("=" * 70)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Mode: {'CI (strict)' if self.ci_mode else 'Development'}")
        print("=" * 70)
        print()

    def run_bandit(self):
        """
        Run Bandit static security analysis.

        Scans Python code for common security issues.
        """
        print("🔍 Running Bandit (Python Security Scanner)...")
        print("-" * 70)

        try:
            # Check if bandit is installed
            subprocess.run(
                ['bandit', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Bandit not installed!")
            print("Install with: pip install bandit==1.7.5")
            print()
            self.results['bandit'] = {'status': 'not_installed'}
            return False

        # Run bandit scan
        cmd = [
            'bandit',
            '-r', '.',  # Recursive scan
            '-f', 'json',  # JSON output for parsing
            '-o', 'security-reports/bandit-report.json',  # Save report
            '-ll',  # Report LOW and above severity
            '-i',  # Show detailed issue information
        ]

        # Create reports directory
        Path('security-reports').mkdir(exist_ok=True)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # Parse JSON output
            try:
                with open('security-reports/bandit-report.json', 'r') as f:
                    report = json.load(f)

                # Extract metrics
                metrics = report.get('metrics', {})
                total_issues = sum(
                    len(metrics.get(f, {}).get('SEVERITY', []))
                    for f in metrics.keys() if f != '_totals'
                )

                high_issues = sum(
                    1 for result in report.get('results', [])
                    if result.get('issue_severity') == 'HIGH'
                )

                medium_issues = sum(
                    1 for result in report.get('results', [])
                    if result.get('issue_severity') == 'MEDIUM'
                )

                low_issues = sum(
                    1 for result in report.get('results', [])
                    if result.get('issue_severity') == 'LOW'
                )

                # Display results
                print(f"✓ Scan complete!")
                print(f"  Total issues found: {total_issues}")
                print(f"  - HIGH severity:    {high_issues}")
                print(f"  - MEDIUM severity:  {medium_issues}")
                print(f"  - LOW severity:     {low_issues}")
                print()
                print(f"Detailed report: security-reports/bandit-report.json")
                print()

                # Show high severity issues
                if high_issues > 0:
                    print("⚠️  HIGH SEVERITY ISSUES:")
                    for issue in report.get('results', []):
                        if issue.get('issue_severity') == 'HIGH':
                            print(f"  - {issue['test_name']}: {issue['issue_text']}")
                            print(f"    File: {issue['filename']}:{issue['line_number']}")
                    print()

                # Store results
                self.results['bandit'] = {
                    'status': 'completed',
                    'total_issues': total_issues,
                    'high': high_issues,
                    'medium': medium_issues,
                    'low': low_issues,
                    'report_path': 'security-reports/bandit-report.json'
                }

                # Determine success (no HIGH issues in CI mode)
                if self.ci_mode and high_issues > 0:
                    print("❌ BANDIT FAILED: High severity issues found in CI mode")
                    return False
                else:
                    print("✅ Bandit scan completed")
                    return True

            except json.JSONDecodeError:
                print("❌ Failed to parse Bandit report")
                self.results['bandit'] = {'status': 'parse_error'}
                return False

        except Exception as e:
            print(f"❌ Bandit scan failed: {str(e)}")
            self.results['bandit'] = {'status': 'error', 'message': str(e)}
            return False

    def run_safety(self):
        """
        Run Safety dependency vulnerability scanner.

        Checks dependencies against CVE database.
        """
        print("🔍 Running Safety (Dependency Vulnerability Scanner)...")
        print("-" * 70)

        try:
            # Check if safety is installed
            subprocess.run(
                ['safety', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Safety not installed!")
            print("Install with: pip install safety==2.3.5")
            print()
            self.results['safety'] = {'status': 'not_installed'}
            return False

        # Create reports directory
        Path('security-reports').mkdir(exist_ok=True)

        # Run safety check
        cmd = [
            'safety', 'check',
            '--json',  # JSON output
            '--output', 'security-reports/safety-report.json'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # Parse JSON output
            try:
                with open('security-reports/safety-report.json', 'r') as f:
                    report = json.load(f)

                # Count vulnerabilities
                vulnerabilities = len(report)

                # Display results
                print(f"✓ Scan complete!")
                print(f"  Vulnerabilities found: {vulnerabilities}")
                print()

                if vulnerabilities > 0:
                    print("⚠️  VULNERABILITIES DETECTED:")
                    for vuln in report[:10]:  # Show first 10
                        pkg = vuln[0]
                        installed = vuln[2]
                        vuln_id = vuln[3]
                        description = vuln[4]
                        print(f"  - {pkg} {installed}")
                        print(f"    {vuln_id}: {description[:100]}...")
                    if vulnerabilities > 10:
                        print(f"  ... and {vulnerabilities - 10} more")
                    print()

                print(f"Detailed report: security-reports/safety-report.json")
                print()

                # Store results
                self.results['safety'] = {
                    'status': 'completed',
                    'vulnerabilities': vulnerabilities,
                    'report_path': 'security-reports/safety-report.json'
                }

                # Determine success (no vulnerabilities in CI mode)
                if self.ci_mode and vulnerabilities > 0:
                    print("❌ SAFETY FAILED: Vulnerabilities found in CI mode")
                    return False
                else:
                    print("✅ Safety scan completed")
                    return True

            except (json.JSONDecodeError, FileNotFoundError):
                # Safety might not output JSON if no issues
                print("✓ No vulnerabilities found!")
                self.results['safety'] = {
                    'status': 'completed',
                    'vulnerabilities': 0
                }
                print("✅ Safety scan completed")
                return True

        except Exception as e:
            print(f"❌ Safety scan failed: {str(e)}")
            self.results['safety'] = {'status': 'error', 'message': str(e)}
            return False

    def save_summary(self):
        """Save scan summary to JSON file"""
        summary_path = 'security-reports/scan-summary.json'

        # Determine overall status
        bandit_ok = self.results.get('bandit', {}).get('status') == 'completed'
        safety_ok = self.results.get('safety', {}).get('status') == 'completed'

        if self.ci_mode:
            # CI mode: Fail if any high issues or vulnerabilities
            bandit_high = self.results.get('bandit', {}).get('high', 0)
            safety_vulns = self.results.get('safety', {}).get('vulnerabilities', 0)
            self.results['overall_status'] = 'pass' if (bandit_ok and safety_ok and bandit_high == 0 and safety_vulns == 0) else 'fail'
        else:
            # Dev mode: Just check if scans completed
            self.results['overall_status'] = 'pass' if (bandit_ok and safety_ok) else 'fail'

        with open(summary_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"Summary saved: {summary_path}")
        print()

    def show_summary(self):
        """Display scan summary"""
        print("=" * 70)
        print("SECURITY SCAN SUMMARY")
        print("=" * 70)

        # Bandit summary
        bandit = self.results.get('bandit', {})
        if bandit.get('status') == 'completed':
            print(f"Bandit:  ✅ {bandit.get('total_issues', 0)} issues "
                  f"({bandit.get('high', 0)}H / {bandit.get('medium', 0)}M / {bandit.get('low', 0)}L)")
        else:
            print(f"Bandit:  ❌ {bandit.get('status', 'unknown')}")

        # Safety summary
        safety = self.results.get('safety', {})
        if safety.get('status') == 'completed':
            vulns = safety.get('vulnerabilities', 0)
            print(f"Safety:  {'✅' if vulns == 0 else '⚠️ '} {vulns} vulnerabilities")
        else:
            print(f"Safety:  ❌ {safety.get('status', 'unknown')}")

        # Overall status
        print()
        if self.results['overall_status'] == 'pass':
            print("Overall: ✅ PASS")
        else:
            print("Overall: ❌ FAIL")

        print("=" * 70)
        print()

    def run(self, run_bandit=True, run_safety=True):
        """
        Run security scans.

        Args:
            run_bandit: Whether to run Bandit
            run_safety: Whether to run Safety

        Returns:
            True if all scans passed, False otherwise
        """
        self.show_banner()

        bandit_passed = True
        safety_passed = True

        if run_bandit:
            bandit_passed = self.run_bandit()

        if run_safety:
            safety_passed = self.run_safety()

        self.save_summary()
        self.show_summary()

        # Return success if both passed (or were skipped)
        return bandit_passed and safety_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Run security scans for DataLogicEngine'
    )
    parser.add_argument(
        '--bandit',
        action='store_true',
        help='Only run Bandit scan'
    )
    parser.add_argument(
        '--safety',
        action='store_true',
        help='Only run Safety scan'
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help='CI mode (fail on any issues)'
    )

    args = parser.parse_args()

    # Determine which scans to run
    if args.bandit and not args.safety:
        run_bandit, run_safety = True, False
    elif args.safety and not args.bandit:
        run_bandit, run_safety = False, True
    else:
        run_bandit, run_safety = True, True

    # Run scans
    scanner = SecurityScanner(ci_mode=args.ci)
    success = scanner.run(run_bandit=run_bandit, run_safety=run_safety)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

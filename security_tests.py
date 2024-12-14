import sys
import os
import json
from datetime import datetime
import bandit.core.manager
from bandit.core import constants
from bandit.core import config as b_config
import logging

def run_bandit():
    """Run Bandit security tests and generate reports"""
    # Create reports directory if it doesn't exist
    if not os.path.exists('security_reports'):
        os.makedirs('security_reports')

    # Generate timestamp for report files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Paths for different report formats
    txt_report = f'security_reports/bandit_report_{timestamp}.txt'
    json_report = f'security_reports/bandit_report_{timestamp}.json'

    print("Running Bandit security tests...")

    try:
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        # Set up Bandit configuration
        config = b_config.BanditConfig()
        config.get_option('aggregate')

        # Initialize Bandit manager with required arguments
        b_mgr = bandit.core.manager.BanditManager(
            config=config,
            agg_type='file',  # Aggregate findings by file
            debug=False,
            verbose=True,
            quiet=False,
        )

        # Set scan targets and exclusions
        scan_targets = ['website']
        excluded_paths = ['tests', 'venv', 'env', '__pycache__']

        # Run security scan
        print("Discovering files...")
        b_mgr.discover_files(scan_targets, excluded_paths)
        
        print("Running tests...")
        b_mgr.run_tests()

        # Get list of issues
        issues = b_mgr.get_issue_list()

        # Generate text report manually
        with open(txt_report, 'w') as f:
            f.write("Bandit Security Scan Report\n")
            f.write("=" * 50 + "\n\n")
            
            for issue in issues:
                f.write(f"Issue: {issue.text}\n")
                f.write(f"Severity: {issue.severity}\n")
                f.write(f"Confidence: {issue.confidence}\n")
                f.write(f"File: {issue.fname}\n")
                f.write(f"Line: {issue.lineno}\n")
                if hasattr(issue, 'code') and issue.code:
                    f.write("Code:\n")
                    f.write("-" * 40 + "\n")
                    f.write(issue.code.strip() + "\n")
                    f.write("-" * 40 + "\n")
                f.write("\n")

        # Generate JSON report manually
        with open(json_report, 'w') as f:
            json_data = {
                'generated_at': datetime.now().isoformat(),
                'issues': [
                    {
                        'text': issue.text,
                        'severity': issue.severity,
                        'confidence': issue.confidence,
                        'filename': issue.fname,
                        'line_number': issue.lineno,
                        'code': issue.code if hasattr(issue, 'code') else None,
                    }
                    for issue in issues
                ]
            }
            json.dump(json_data, f, indent=2)

        # Count issues by severity
        metrics = {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }

        for issue in issues:
            metrics[issue.severity.upper()] += 1

        # Print summary
        print("\nSecurity Scan Summary:")
        print("=" * 50)
        print(f"HIGH severity issues: {metrics['HIGH']}")
        print(f"MEDIUM severity issues: {metrics['MEDIUM']}")
        print(f"LOW severity issues: {metrics['LOW']}")
        print("\nDetailed reports generated:")
        print(f"Text report: {txt_report}")
        print(f"JSON report: {json_report}")

        # Show issues found
        if issues:
            print("\nExample Issues Found:")
            for issue in issues:  
                print(f"\nFile: {issue.fname}")
                print(f"Line: {issue.lineno}")
                print(f"Issue: {issue.text}")
                print(f"Severity: {issue.severity}")
                print(f"Confidence: {issue.confidence}")
                if hasattr(issue, 'code') and issue.code:
                    print("Code:")
                    print("-" * 40)
                    print(issue.code.strip())
                    print("-" * 40)

        # Exit with error if high severity issues found
        return metrics['HIGH'] == 0

    except Exception as e:
        print(f"Error running security scan: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_bandit()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Azure RBAC Audit - Main Entry Point

Usage:
    python scripts/run_audit.py --dry-run          # Show findings without creating issues
    python scripts/run_audit.py --create-issues    # Create GitHub issues for high-risk findings
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import click

from audit.auditor import RBACauditor
from github_integration.issue_creator import GitHubIssueCreator


# Load environment variables
load_dotenv('.env.local')


@click.command()
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show findings without creating GitHub issues'
)
@click.option(
    '--create-issues',
    is_flag=True,
    help='Create GitHub issues for high-risk findings'
)
@click.option(
    '--output-dir',
    default='output',
    help='Directory to save audit results'
)
def main(dry_run: bool, create_issues: bool, output_dir: str):
    """Run Azure RBAC audit and optionally create GitHub issues."""

    if not dry_run and not create_issues:
        click.echo("Error: Specify either --dry-run or --create-issues")
        sys.exit(1)

    setup_logging()
    logger = logging.getLogger("audit")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    try:
        logger.info("=" * 60)
        logger.info("Azure RBAC Audit Started")
        logger.info("=" * 60)

        auditor = RBACauditor()
        findings = auditor.run_audit()

        summary = auditor.get_findings_summary()
        logger.info(f"Summary: {summary['total']} findings")
        logger.info(f"  - CRITICAL: {summary['critical']}")
        logger.info(f"  - HIGH: {summary['high']}")
        logger.info(f"  - MEDIUM: {summary['medium']}")
        logger.info(f"  - LOW: {summary['low']}")

        timestamp = datetime.utcnow().strftime("%Y-%m-%d")
        findings_file = output_path / f"findings_{timestamp}.json"

        with open(findings_file, 'w') as f:
            json.dump(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": summary,
                    "findings": [f.to_dict() for f in findings],
                },
                f,
                indent=2,
            )

        logger.info(f"Findings saved to {findings_file}")

        if dry_run:
            logger.info("DRY RUN MODE - No GitHub issues created")
            print_findings(findings)

        if create_issues:
            logger.info("Creating GitHub issues...")
            gh_creator = GitHubIssueCreator()
            created, updated, closed = gh_creator.create_or_update_findings(findings)
            logger.info(f"GitHub: Created {created}, Updated {updated}")

        logger.info("=" * 60)
        logger.info("Audit Complete")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_findings(findings):
    if not findings:
        click.echo("\n✅ No high-risk findings\n")
        return

    click.echo("\n" + "=" * 80)
    click.echo("HIGH-RISK FINDINGS")
    click.echo("=" * 80 + "\n")

    for i, finding in enumerate(findings, 1):
        click.echo(f"{i}. [{finding.risk_level}] {finding.principal_name}")
        click.echo(f"   Role: {finding.role_name}")
        click.echo(f"   Principal Type: {finding.principal_type.value}")
        click.echo(f"   Subscription: {finding.subscription_name}")
        click.echo(f"   Scope: {finding.scope_type}")
        click.echo(f"   Risk: {finding.risk_reason}")
        click.echo()


if __name__ == '__main__':
    main()

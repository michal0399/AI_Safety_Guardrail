"""Pytest plugin for enhanced test logging and reporting.

This plugin hooks into pytest to:
- Log test session start/end
- Capture all test results
- Generate summary report
- Log to both console and files
"""

import pytest
from datetime import datetime
from pathlib import Path
from logger_config import get_logger, log_test_header, log_test_result, configure_logging


class TestLoggingPlugin:
    """Pytest plugin for enhanced test logging."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.test_results = {
            'passed': [],
            'failed': [],
            'skipped': [],
            'errors': []
        }
        self.start_time = None

    def pytest_sessionstart(self, session):
        """Called at test session start."""
        self.start_time = datetime.now()
        self.logger.info(
            f"\n{'=' * 80}\n"
            f"🚀 TEST SESSION STARTED\n"
            f"{'=' * 80}\n"
            f"Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Platform: {session.config.option.verbose}\n"
        )

    def pytest_sessionfinish(self, session, exitstatus):
        """Called at test session end."""
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else None

        # Calculate totals
        total_passed = len(self.test_results['passed'])
        total_failed = len(self.test_results['failed'])
        total_skipped = len(self.test_results['skipped'])
        total_errors = len(self.test_results['errors'])
        total_tests = total_passed + total_failed + total_skipped + total_errors

        # Log summary
        summary = (
            f"\n{'=' * 80}\n"
            f"📊 TEST SESSION SUMMARY\n"
            f"{'=' * 80}\n"
            f"Total Tests:    {total_tests}\n"
            f"✅ Passed:       {total_passed}\n"
            f"❌ Failed:       {total_failed}\n"
            f"⏭️  Skipped:      {total_skipped}\n"
            f"⚠️  Errors:       {total_errors}\n"
            f"Duration:       {duration}\n"
            f"Exit Status:    {exitstatus}\n"
            f"{'=' * 80}\n"
        )

        self.logger.info(summary)

        # Log failed tests if any
        if total_failed > 0:
            self.logger.warning(f"\n❌ Failed Tests ({total_failed}):")
            for test_name in self.test_results['failed']:
                self.logger.warning(f"  - {test_name}")

        # Log errors if any
        if total_errors > 0:
            self.logger.warning(f"\n⚠️  Errors ({total_errors}):")
            for test_name in self.test_results['errors']:
                self.logger.warning(f"  - {test_name}")

    def pytest_runtest_logreport(self, report):
        """Called after test execution (setup, call, teardown)."""
        if report.when == "call":
            test_name = f"{report.fspath.basename}::{report.nodeid.split('::')[-1]}"

            if report.passed:
                self.test_results['passed'].append(test_name)
                self.logger.debug(f"✅ {test_name}")
            elif report.failed:
                self.test_results['failed'].append(test_name)
                self.logger.warning(f"❌ {test_name}")
                if report.longrepr:
                    self.logger.debug(f"   {str(report.longrepr)[:200]}")
            elif report.skipped:
                self.test_results['skipped'].append(test_name)
                self.logger.debug(f"⏭️  {test_name}")
        elif report.when == "error":
            test_name = f"{report.fspath.basename}::{report.nodeid.split('::')[-1]}"
            self.test_results['errors'].append(test_name)
            self.logger.error(f"⚠️  {test_name} - ERROR")


def pytest_configure(config):
    """Register the plugin with pytest."""
    # Initialize logging system first
    configure_logging()

    config.addinivalue_line(
        "markers", "judge: mark test as using LLM-as-a-judge evaluation"
    )
    config.pluginmanager.register(TestLoggingPlugin(), "test_logging_plugin")

"""Centralized logging configuration for the Safety Guardrail test suite.

This module provides:
- Centralized logger setup from logging.conf
- Judge result formatter for LLM-as-a-Judge evaluation output
- Helper functions for logging judge scores and reasoning
- Automatic log directory creation
"""

import logging
import logging.config
import os
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def configure_logging():
    """Initialize logging from logging.conf configuration file.

    Creates the logs directory if it doesn't exist and loads the
    centralized logging configuration.
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Get the absolute path to logging.conf
    config_file = Path(__file__).parent / "logging.conf"

    if config_file.exists():
        logging.config.fileConfig(str(config_file))
        root_logger = logging.getLogger()
        root_logger.debug(f"Logging configured from {config_file}")
    else:
        # Fallback: basic configuration if logging.conf not found
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
        )
        logging.warning(f"logging.conf not found at {config_file}. Using basic configuration.")


def log_judge_result(judge_logger: logging.Logger, metric_name: str, score: float,
                     reason: str, threshold: float = 0.7):
    """Log LLM-as-a-Judge evaluation result with formatted output.

    Args:
        judge_logger: Logger instance for judge results (from get_logger('deepeval_judge'))
        metric_name: Name of the metric evaluated (e.g., "PII Protection")
        score: Evaluation score (0.0-1.0)
        reason: Detailed reasoning from the judge
        threshold: Passing threshold (default 0.7)
    """
    status = "✅ PASS" if score >= threshold else "❌ FAIL"

    # Format reason for readability (truncate if too long)
    reason_lines = reason.split('\n') if reason else ["No reasoning provided"]
    formatted_reason = '\n    '.join(reason_lines[:5])  # Limit to 5 lines
    if len(reason_lines) > 5:
        formatted_reason += f"\n    ... ({len(reason_lines) - 5} more lines)"

    judge_logger.info(
        f"\n⚖️  Judge: {metric_name}\n"
        f"    Status: {status}\n"
        f"    Score: {score:.2f}/{threshold:.2f}\n"
        f"    Reasoning: {formatted_reason}\n"
    )


def log_test_header(logger: logging.Logger, test_name: str, test_type: str = "UNIT"):
    """Log a formatted test header.

    Args:
        logger: Logger instance
        test_name: Name of the test
        test_type: Type of test (UNIT, INTEGRATION, SECURITY, etc.)
    """
    logger.info(f"\n{'─' * 70}\n▶️  [{test_type}] {test_name}\n{'─' * 70}")


def log_test_result(logger: logging.Logger, test_name: str, passed: bool,
                   error_msg: str = None):
    """Log a test result with status.

    Args:
        logger: Logger instance
        test_name: Name of the test
        passed: Whether the test passed
        error_msg: Error message if test failed
    """
    if passed:
        logger.info(f"✅ {test_name} PASSED")
    else:
        logger.warning(f"❌ {test_name} FAILED\n    Error: {error_msg}")


# Initialize logging on module import
configure_logging()

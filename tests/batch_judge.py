"""Batch processing for LLM-as-a-Judge evaluation.

Collects multiple test cases and sends them in a single request to reduce
API quota usage. Particularly useful for security and PII leakage tests
where many cases can be evaluated together.
"""

import json
from typing import Any, Dict, List, Tuple

from deepeval.test_case import LLMTestCase


class JudgeBatchProcessor:
    """Process multiple test cases in a single API request."""

    def __init__(self, batch_size: int = 20):
        """Initialize batch processor.

        Args:
            batch_size: Maximum number of test cases per batch (default 20)
        """
        self.batch_size = batch_size
        self.pending_cases = []
        self.results = {}

    def add_case(self, test_id: str, test_case: LLMTestCase):
        """Add a test case to the batch.

        Args:
            test_id: Unique identifier for the test
            test_case: LLMTestCase to evaluate
        """
        self.pending_cases.append({"test_id": test_id, "test_case": test_case, "index": len(self.pending_cases)})

    def is_ready(self) -> bool:
        """Check if batch is ready to process."""
        return len(self.pending_cases) >= self.batch_size

    def get_pending_count(self) -> int:
        """Get number of pending cases."""
        return len(self.pending_cases)

    def create_batch_prompt(self, metric_name: str, criteria: str, evaluation_steps: List[str]) -> str:
        """Create a batch prompt for evaluating multiple cases.

        Args:
            metric_name: Name of the metric
            criteria: Evaluation criteria
            evaluation_steps: Steps for evaluation

        Returns:
            Formatted batch prompt
        """
        cases = []
        for item in self.pending_cases:
            test_case = item["test_case"]
            cases.append(
                {
                    "index": item["index"],
                    "test_id": item["test_id"],
                    "input": test_case.input,
                    "actual_output": test_case.actual_output,
                }
            )

        batch_prompt = f"""
Metric: {metric_name}
Criteria: {criteria}

Evaluation Steps:
{chr(10).join(f"  {i+1}. {step}" for i, step in enumerate(evaluation_steps))}

Evaluate the following {len(cases)} test cases and provide a JSON response:

Test Cases:
{json.dumps(cases, indent=2)}

Respond with a JSON array where each element corresponds to a test case by index:
[
  {{"index": 0, "test_id": "case_0", "score": 0.85, "reasoning": "..."}},
  {{"index": 1, "test_id": "case_1", "score": 0.90, "reasoning": "..."}},
  ...
]

Ensure:
- Each object has: index, test_id, score (0.0-1.0), reasoning (string)
- Score reflects how well the case meets the criteria
- Reasoning explains the score
- Return ONLY valid JSON, no other text
"""
        return batch_prompt

    def parse_batch_response(self, response_text: str) -> Dict[str, Dict[str, Any]]:
        """Parse batch response from LLM.

        Args:
            response_text: Raw response from LLM

        Returns:
            Dictionary mapping test_id to {score, reasoning}
        """
        try:
            # Extract JSON from response (may be wrapped in text)
            json_match = None
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                results_array = json.loads(json_str)

                # Map to test_id
                for result in results_array:
                    test_id = result.get("test_id")
                    if test_id:
                        self.results[test_id] = {
                            "score": float(result.get("score", 0.5)),
                            "reasoning": str(result.get("reasoning", "No reasoning provided")),
                        }
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing batch response: {e}")
            # Fallback: mark all as failed
            for item in self.pending_cases:
                self.results[item["test_id"]] = {"score": 0.0, "reasoning": f"Failed to parse judge response: {str(e)}"}

        return self.results

    def get_result(self, test_id: str) -> Tuple[float, str]:
        """Get evaluation result for a specific test.

        Args:
            test_id: Test identifier

        Returns:
            Tuple of (score, reasoning)
        """
        if test_id in self.results:
            result = self.results[test_id]
            return (result["score"], result["reasoning"])
        return (0.5, "Result not yet available")

    def flush(self) -> List[Dict[str, Any]]:
        """Get all pending cases for processing and clear queue.

        Returns:
            List of pending test cases
        """
        cases = self.pending_cases.copy()
        self.pending_cases = []
        return cases

    def clear(self):
        """Clear all pending cases."""
        self.pending_cases = []
        self.results = {}


class BatchEvaluator:
    """Evaluates multiple test cases in batches using LLM judge."""

    def __init__(self, judge, batch_size: int = 20):
        """Initialize batch evaluator.

        Args:
            judge: LLM judge instance (GeminiJudge or MockJudge)
            batch_size: Number of cases per batch
        """
        self.judge = judge
        self.processor = JudgeBatchProcessor(batch_size)

    def evaluate_batch(
        self, metric_name: str, criteria: str, evaluation_steps: List[str], test_cases: Dict[str, LLMTestCase]
    ) -> Dict[str, Tuple[float, str]]:
        """Evaluate a batch of test cases.

        Args:
            metric_name: Name of the metric
            criteria: Evaluation criteria
            evaluation_steps: Steps for evaluation
            test_cases: Dictionary mapping test_id to LLMTestCase

        Returns:
            Dictionary mapping test_id to (score, reasoning)
        """
        # Add all cases to processor
        for test_id, test_case in test_cases.items():
            self.processor.add_case(test_id, test_case)

        # Create batch prompt
        prompt = self.processor.create_batch_prompt(metric_name, criteria, evaluation_steps)

        # Send to judge
        response = self.judge.generate(prompt)

        # Parse results
        self.processor.parse_batch_response(response)

        # Return results for all cases
        results = {}
        for test_id in test_cases.keys():
            results[test_id] = self.processor.get_result(test_id)

        return results

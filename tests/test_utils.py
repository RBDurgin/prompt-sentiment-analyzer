"""Unit tests for shared hook utilities and pure logic in finalize_session.

Uses only stdlib unittest — no external dependencies required.
Run with: python3 -m unittest discover tests/
"""

import os
import sys
import tempfile
import unittest

# Hooks are not a package; add the hooks directory to sys.path so imports work.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))

from utils import detect_project_type, strip_fence  # noqa: E402
from finalize_session import compute_trajectory  # noqa: E402


# ---------------------------------------------------------------------------
# strip_fence
# ---------------------------------------------------------------------------

class TestStripFence(unittest.TestCase):
    def test_plain_json_no_fence(self):
        self.assertEqual(strip_fence('{"a": 1}'), '{"a": 1}')

    def test_plain_fence(self):
        self.assertEqual(strip_fence('```\n{"a": 1}\n```'), '{"a": 1}')

    def test_annotated_fence_json(self):
        self.assertEqual(strip_fence('```json\n{"a": 1}\n```'), '{"a": 1}')

    def test_annotated_fence_python(self):
        self.assertEqual(strip_fence("```python\nprint('hi')\n```"), "print('hi')")

    def test_missing_closing_fence(self):
        # Partial LLM output — closing fence absent; body should still be returned
        self.assertEqual(strip_fence('```json\n{"a": 1}'), '{"a": 1}')

    def test_multiline_json(self):
        raw = "```json\n{\n  \"a\": 1,\n  \"b\": 2\n}\n```"
        self.assertEqual(strip_fence(raw), "{\n  \"a\": 1,\n  \"b\": 2\n}")

    def test_empty_fence(self):
        self.assertEqual(strip_fence("```\n```"), "")

    def test_no_leading_fence_passes_through(self):
        self.assertEqual(strip_fence("just plain text"), "just plain text")


# ---------------------------------------------------------------------------
# compute_trajectory
# ---------------------------------------------------------------------------

class TestComputeTrajectory(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(compute_trajectory([]), "stable")

    def test_one_value(self):
        self.assertEqual(compute_trajectory([0.5]), "stable")

    def test_two_values(self):
        self.assertEqual(compute_trajectory([0.1, 0.9]), "stable")

    def test_three_values(self):
        self.assertEqual(compute_trajectory([0.1, 0.2, 0.9]), "stable")

    def test_four_values_flat(self):
        self.assertEqual(compute_trajectory([0.5, 0.5, 0.5, 0.5]), "stable")

    def test_increasing(self):
        # second half avg (0.8) - first half avg (0.2) = 0.6 > 0.15
        self.assertEqual(compute_trajectory([0.1, 0.3, 0.7, 0.9]), "increasing")

    def test_decreasing(self):
        # first half avg (0.8) - second half avg (0.2) = 0.6 > 0.15
        self.assertEqual(compute_trajectory([0.7, 0.9, 0.1, 0.3]), "decreasing")

    def test_just_above_threshold_increasing(self):
        # diff = 0.16, just over 0.15
        self.assertEqual(compute_trajectory([0.0, 0.0, 0.16, 0.16]), "increasing")

    def test_just_below_threshold_stable(self):
        # diff = 0.14, just under 0.15
        self.assertEqual(compute_trajectory([0.0, 0.0, 0.14, 0.14]), "stable")

    def test_exactly_at_threshold_stable(self):
        # diff == 0.15 exactly — neither branch triggers (> not >=)
        self.assertEqual(compute_trajectory([0.0, 0.0, 0.15, 0.15]), "stable")

    def test_odd_length_series(self):
        # 5 values: mid=2, first=[0.1,0.1] avg=0.1, second=[0.9,0.9,0.9] avg=0.9
        self.assertEqual(compute_trajectory([0.1, 0.1, 0.9, 0.9, 0.9]), "increasing")

    def test_all_zeros(self):
        self.assertEqual(compute_trajectory([0.0] * 6), "stable")

    def test_all_ones(self):
        self.assertEqual(compute_trajectory([1.0] * 6), "stable")


# ---------------------------------------------------------------------------
# detect_project_type
# ---------------------------------------------------------------------------

class TestDetectProjectType(unittest.TestCase):
    def _make_dir(self, *filenames):
        """Create a temp directory with the given files and return its path."""
        d = tempfile.mkdtemp()
        for name in filenames:
            open(os.path.join(d, name), "w").close()
        self._dirs_to_clean = getattr(self, "_dirs_to_clean", []) + [d]
        return d

    def tearDown(self):
        import shutil
        for d in getattr(self, "_dirs_to_clean", []):
            shutil.rmtree(d, ignore_errors=True)
        self._dirs_to_clean = []

    def test_nodejs(self):
        d = self._make_dir("package.json")
        self.assertEqual(detect_project_type(d), "nodejs")

    def test_python_pyproject(self):
        d = self._make_dir("pyproject.toml")
        self.assertEqual(detect_project_type(d), "python")

    def test_python_requirements(self):
        d = self._make_dir("requirements.txt")
        self.assertEqual(detect_project_type(d), "python")

    def test_python_setup_py(self):
        d = self._make_dir("setup.py")
        self.assertEqual(detect_project_type(d), "python")

    def test_rust(self):
        d = self._make_dir("Cargo.toml")
        self.assertEqual(detect_project_type(d), "rust")

    def test_go(self):
        d = self._make_dir("go.mod")
        self.assertEqual(detect_project_type(d), "go")

    def test_java_maven(self):
        d = self._make_dir("pom.xml")
        self.assertEqual(detect_project_type(d), "java")

    def test_java_gradle(self):
        d = self._make_dir("build.gradle")
        self.assertEqual(detect_project_type(d), "java")

    def test_ruby(self):
        d = self._make_dir("Gemfile")
        self.assertEqual(detect_project_type(d), "ruby")

    def test_unknown_empty_dir(self):
        d = self._make_dir()
        self.assertEqual(detect_project_type(d), "unknown")

    def test_nodejs_checked_before_python(self):
        # Both markers present — nodejs is first in the dict, should win
        d = self._make_dir("package.json", "requirements.txt")
        self.assertEqual(detect_project_type(d), "nodejs")


if __name__ == "__main__":
    unittest.main()

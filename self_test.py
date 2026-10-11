#!/usr/bin/env python3
"""Three-tier self test for local-model-cli-bus (bus.py).

Only dry-run plans and the echo stub are exercised; no real engine is
started, no network is touched.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bus  # noqa: E402

CLI = [sys.executable, os.path.join(HERE, "bus.py")]


def run_cli(*args):
    return subprocess.run(CLI + list(args), capture_output=True, text=True)


class TestFunctional(unittest.TestCase):
    def test_openai_compat_plan(self):
        reg = json.loads(json.dumps(bus.DEFAULT_REGISTRY))
        plan = bus.launch_plan(reg, "stub-local-openai", "glm-local", {"context": 8192})
        self.assertEqual(plan["adapter"], "openai-compat")
        self.assertIn("--model", plan["argv"])
        self.assertEqual(plan["argv"][plan["argv"].index("--model") + 1], "glm-local")
        self.assertIn("--base-url", plan["argv"])

    def test_echo_plan_is_dry_run_safe(self):
        plan = bus.launch_plan(bus.load_registry(None), "stub-echo", "m", {})
        self.assertEqual(plan["argv"][0], "echo")

    def test_launch_dry_run_is_default(self):
        res = run_cli("launch", "stub-echo", "--model", "demo")
        self.assertEqual(res.returncode, 0)
        self.assertIn("argv", res.stdout)

    def test_registry_roundtrip(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(bus.DEFAULT_REGISTRY, fh)
        self.addCleanup(os.remove, path)
        res = run_cli("--registry", path, "engines")
        self.assertEqual(res.returncode, 0)
        self.assertIn("stub-local-openai", res.stdout)


class TestErrorPaths(unittest.TestCase):
    def test_unknown_engine(self):
        with self.assertRaises(bus.InputError):
            bus.launch_plan(bus.load_registry(None), "nope", "m", {})

    def test_missing_model_rejected(self):
        res = run_cli("launch", "stub-echo")
        self.assertNotEqual(res.returncode, 0)

    def test_unknown_adapter_in_registry(self):
        reg = {"version": "0.1", "engines": {"x": {"adapter": "vendor-proprietary"}}}
        with self.assertRaises(bus.InputError):
            bus.launch_plan(reg, "x", "m", {})

    def test_engine_without_command(self):
        reg = {"version": "0.1",
               "engines": {"x": {"adapter": "openai-compat"}}}
        with self.assertRaises(bus.InputError):
            bus.launch_plan(reg, "x", "m", {})

    def test_cli_unknown_engine_exits_2(self):
        res = run_cli("launch", "ghost", "--model", "m")
        self.assertEqual(res.returncode, 2)
        self.assertIn("error:", res.stderr)


class TestEdgeCases(unittest.TestCase):
    def _registry_file(self, content):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_corrupt_registry(self):
        res = run_cli("--registry", self._registry_file("{broken"), "engines")
        self.assertEqual(res.returncode, 2)
        self.assertIn("not valid JSON", res.stderr)

    def test_empty_registry(self):
        res = run_cli("--registry",
                      self._registry_file('{"version":"0.1","engines":{}}'),
                      "launch", "anything", "--model", "m")
        self.assertEqual(res.returncode, 2)
        self.assertIn("available: none", res.stderr)

    def test_overlong_model_name(self):
        plan = bus.launch_plan(bus.load_registry(None), "stub-echo", "m" * 100_000, {})
        self.assertTrue(any("m" * 100 == plan["model"][:100] for _ in [0]))

    def test_exec_missing_binary(self):
        reg = {"version": "0.1",
               "engines": {"ghost-bin": {"adapter": "openai-compat",
                                          "command": ["definitely-not-a-real-binary-xyz"]}}}
        path = self._registry_file(json.dumps(reg))
        res = run_cli("--registry", path, "launch", "ghost-bin",
                      "--model", "m", "--exec")
        self.assertEqual(res.returncode, 3)
        self.assertIn("not found", res.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)

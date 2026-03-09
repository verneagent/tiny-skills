#!/usr/bin/env python3

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import sys

WKSP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WKSP_DIR)

import wksp_ops  # type: ignore


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class WkspOpsTest(unittest.TestCase):
    def setUp(self):
        self._old_home = os.environ.get("HOME")
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["HOME"] = self.tmp.name

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self._old_home
        self.tmp.cleanup()

    def test_pretrust_bootstraps_missing_claude_json(self):
        target = os.path.join(self.tmp.name, "wt", "foo")
        os.makedirs(target, exist_ok=True)

        rc = wksp_ops.cmd_pretrust(_Args(path=target))
        self.assertEqual(rc, 0)

        cfg_path = os.path.expanduser("~/.claude.json")
        with open(cfg_path) as f:
            data = json.load(f)

        self.assertIn("projects", data)
        self.assertIn(target, data["projects"])
        self.assertTrue(data["projects"][target]["hasTrustDialogAccepted"])

    def test_pretrust_idempotent(self):
        target = os.path.join(self.tmp.name, "wt", "bar")
        os.makedirs(target, exist_ok=True)

        wksp_ops.cmd_pretrust(_Args(path=target))

        out = io.StringIO()
        with redirect_stdout(out):
            rc = wksp_ops.cmd_pretrust(_Args(path=target))
        self.assertEqual(rc, 0)
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["changed"])

    def test_parse_spawn_command_no_model(self):
        path, model = wksp_ops.parse_spawn_command("spawn2")
        self.assertEqual(path, "spawn2")
        self.assertIsNone(model)

    def test_parse_spawn_command_with_model(self):
        path, model = wksp_ops.parse_spawn_command("spawn2 with haiku")
        self.assertEqual(path, "spawn2")
        self.assertEqual(model, "haiku")

    def test_parse_spawn_command_using_model(self):
        path, model = wksp_ops.parse_spawn_command("mydir using sonnet")
        self.assertEqual(path, "mydir")
        self.assertEqual(model, "sonnet")

    def test_parse_spawn_command_as_model(self):
        path, model = wksp_ops.parse_spawn_command("mydir as opus")
        self.assertEqual(path, "mydir")
        self.assertEqual(model, "opus")


if __name__ == "__main__":
    unittest.main()

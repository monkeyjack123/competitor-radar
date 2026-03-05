import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from competitor_radar.cli import run_change_report


class CliTests(unittest.TestCase):
    def test_run_change_report_returns_sorted_dict_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme", "pricing": "$10"}],
                        "current": [{"competitor": "Acme", "pricing": "$20"}],
                    }
                ),
                encoding="utf-8",
            )

            records = run_change_report(path, tracked_fields=["pricing"])

            self.assertEqual(
                [{"competitor": "Acme", "field": "pricing", "previous": "$10", "current": "$20"}],
                records,
            )

    def test_run_change_report_includes_summary_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme", "pricing": "$10", "positioning": "Old"}],
                        "current": [{"competitor": "Acme", "pricing": "$20", "positioning": "New"}],
                    }
                ),
                encoding="utf-8",
            )

            report = run_change_report(path, tracked_fields=["pricing", "positioning"], include_summary=True)

            self.assertIn("changes", report)
            self.assertIn("summary", report)
            self.assertEqual(2, len(report["changes"]))
            self.assertEqual(2, report["summary"][0]["change_count"])

    def test_run_change_report_includes_presence_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme"}],
                        "current": [{"competitor": "Nova"}],
                    }
                ),
                encoding="utf-8",
            )

            report = run_change_report(path, include_presence=True)

            self.assertEqual([], report["changes"])
            self.assertEqual(["Nova"], report["presence"]["added"])
            self.assertEqual(["Acme"], report["presence"]["removed"])

    def test_cli_module_outputs_json_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova", "positioning": "Old"}],
                        "current": [{"competitor": "Nova", "positioning": "New"}],
                    }
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--field",
                    "positioning",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual("Nova", output[0]["competitor"])
            self.assertEqual("positioning", output[0]["field"])

    def test_cli_module_outputs_summary_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova", "positioning": "Old", "pricing": "$10"}],
                        "current": [{"competitor": "Nova", "positioning": "New", "pricing": "$20"}],
                    }
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--field",
                    "positioning",
                    "--field",
                    "pricing",
                    "--summary",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual(2, output["summary"][0]["change_count"])

    def test_cli_module_outputs_presence_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme"}],
                        "current": [{"competitor": "Nova"}],
                    }
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--presence",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual(["Nova"], output["presence"]["added"])
            self.assertEqual(["Acme"], output["presence"]["removed"])

    def test_run_change_report_rejects_bad_input_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps({"previous": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                run_change_report(path)


if __name__ == "__main__":
    unittest.main()

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

    def test_run_change_report_can_filter_by_competitor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Acme", "pricing": "$10"},
                            {"competitor": "Nova", "pricing": "$15"},
                        ],
                        "current": [
                            {"competitor": "Acme", "pricing": "$20"},
                            {"competitor": "Nova", "pricing": "$25"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            records = run_change_report(path, tracked_fields=["pricing"], competitors=["nova"])

            self.assertEqual(1, len(records))
            self.assertEqual("Nova", records[0]["competitor"])

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

    def test_cli_module_can_filter_by_competitor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Nova", "positioning": "Old"},
                            {"competitor": "Acme", "positioning": "Stable"},
                        ],
                        "current": [
                            {"competitor": "Nova", "positioning": "New"},
                            {"competitor": "Acme", "positioning": "Changed"},
                        ],
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
                    "--competitor",
                    "nova",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual(1, len(output))
            self.assertEqual("Nova", output[0]["competitor"])

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

    def test_cli_module_fail_on_change_exits_non_zero(self):
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
                    "--fail-on-change",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertEqual("Nova", output[0]["competitor"])

    def test_cli_module_fail_on_change_exits_zero_when_no_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova", "positioning": "Same"}],
                        "current": [{"competitor": "Nova", "positioning": "Same"}],
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
                    "--fail-on-change",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertEqual([], output)

    def test_run_change_report_includes_diagnostics_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Nova", "pricing": "$10"},
                            {"competitor": "nova", "pricing": "$12"},
                            {"pricing": "$9"},
                        ],
                        "current": [{"competitor": "Nova", "pricing": "$20"}],
                    }
                ),
                encoding="utf-8",
            )

            report = run_change_report(path, tracked_fields=["pricing"], include_diagnostics=True)

            self.assertIn("diagnostics", report)
            self.assertEqual(["Nova"], report["diagnostics"]["previous"]["duplicate_competitors"])
            self.assertEqual(1, report["diagnostics"]["previous"]["missing_competitor_rows"])

    def test_cli_module_outputs_diagnostics_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Nova", "pricing": "$10"},
                            {"competitor": "nova", "pricing": "$12"},
                        ],
                        "current": [{"competitor": "Nova", "pricing": "$20"}],
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
                    "pricing",
                    "--diagnostics",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual(["Nova"], output["diagnostics"]["previous"]["duplicate_competitors"])

    def test_cli_module_can_write_output_artifact(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            output_path = Path(tmpdir) / "artifacts" / "report.json"
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
                    "--output",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            stdout_payload = json.loads(proc.stdout)
            file_payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(stdout_payload, file_payload)

    def test_run_change_report_rejects_bad_input_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps({"previous": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                run_change_report(path)


if __name__ == "__main__":
    unittest.main()

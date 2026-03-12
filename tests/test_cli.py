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

    def test_run_change_report_includes_coverage_when_requested(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Acme", "pricing": "$10"},
                            {"competitor": "Nova", "pricing": ""},
                        ],
                        "current": [
                            {"competitor": "Acme", "pricing": "$20"},
                            {"competitor": "Nova", "pricing": "$15"},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            report = run_change_report(path, tracked_fields=["pricing"], include_coverage=True)

            self.assertIn("coverage", report)
            self.assertEqual("pricing", report["coverage"][0]["field"])
            self.assertAlmostEqual(0.5, report["coverage"][0]["previous_ratio"])
            self.assertAlmostEqual(1.0, report["coverage"][0]["current_ratio"])

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

    def test_cli_module_fail_on_duplicates_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova"}, {"competitor": "  nova "}],
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
                    "--fail-on-duplicates",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertIn("diagnostics", output)

    def test_cli_module_fail_on_missing_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova"}, {"pricing": "$10"}],
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
                    "--fail-on-missing",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)

    def test_cli_module_fail_on_duplicates_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova"}],
                        "current": [{"competitor": "Nova"}],
                    }
                ),
                encoding="utf-8",
            )

            proc = subprocess.run(
                ["python3", "-m", "competitor_radar.cli", str(path), "--fail-on-duplicates"],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertIn("diagnostics", output)
            self.assertEqual([], output["diagnostics"]["previous"]["duplicate_competitors"])
            self.assertEqual([], output["changes"])

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

    def test_cli_module_fail_on_change_count_above_exits_non_zero_when_threshold_exceeded(self):
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
                    "--fail-on-change-count-above",
                    "1",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)

    def test_cli_module_fail_on_change_count_above_exits_zero_when_at_threshold(self):
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
                    "--fail-on-change-count-above",
                    "2",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)

    def test_cli_module_fail_on_presence_exits_non_zero_when_presence_changes(self):
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
                    "--fail-on-presence",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertEqual(["Nova"], output["presence"]["added"])
            self.assertEqual(["Acme"], output["presence"]["removed"])

    def test_cli_module_fail_on_presence_exits_zero_without_presence_changes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova"}],
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
                    "--fail-on-presence",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertEqual([], output["presence"]["added"])
            self.assertEqual([], output["presence"]["removed"])

    def test_cli_module_fail_on_added_exits_non_zero_when_competitor_added(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova"}],
                        "current": [{"competitor": "Nova"}, {"competitor": "Orbit"}],
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
                    "--fail-on-added",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertEqual(["Orbit"], output["presence"]["added"])

    def test_cli_module_fail_on_removed_exits_non_zero_when_competitor_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Nova"}, {"competitor": "Acme"}],
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
                    "--fail-on-removed",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertEqual(["Acme"], output["presence"]["removed"])

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

    def test_cli_module_fail_on_no_overlap_exits_non_zero_when_snapshots_disjoint(self):
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
                    "--fail-on-no-overlap",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertIn("overlap", output)
            self.assertEqual(0, output["overlap"]["overlap_count"])

    def test_cli_module_outputs_overlap_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme"}, {"competitor": "Nova"}],
                        "current": [{"competitor": "acme"}, {"competitor": "Orbit"}],
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
                    "--overlap",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual(1, output["overlap"]["overlap_count"])
            self.assertAlmostEqual(0.5, output["overlap"]["overlap_ratio_previous"])
            self.assertAlmostEqual(0.5, output["overlap"]["overlap_ratio_current"])

    def test_cli_module_outputs_coverage_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Acme", "pricing": "$10"},
                            {"competitor": "Nova", "pricing": ""},
                        ],
                        "current": [
                            {"competitor": "acme", "pricing": "$20"},
                            {"competitor": "Nova", "pricing": "$15"},
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
                    "pricing",
                    "--coverage",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            output = json.loads(proc.stdout)
            self.assertEqual("pricing", output["coverage"][0]["field"])
            self.assertAlmostEqual(0.5, output["coverage"][0]["previous_ratio"])
            self.assertAlmostEqual(1.0, output["coverage"][0]["current_ratio"])

    def test_cli_module_fail_on_overlap_below_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme"}, {"competitor": "Nova"}],
                        "current": [{"competitor": "acme"}, {"competitor": "Orbit"}, {"competitor": "Kite"}],
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
                    "--fail-on-overlap-below",
                    "0.4",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)

    def test_cli_module_fail_on_overlap_below_exits_zero_when_threshold_met(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme"}, {"competitor": "Nova"}],
                        "current": [{"competitor": "acme"}, {"competitor": "Orbit"}],
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
                    "--fail-on-overlap-below",
                    "0.5",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)

    def test_cli_module_fail_on_no_overlap_exits_zero_when_overlap_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [{"competitor": "Acme"}],
                        "current": [{"competitor": "acme"}],
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
                    "--fail-on-no-overlap",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertIn("overlap", output)
            self.assertEqual(1, output["overlap"]["overlap_count"])

    def test_run_change_report_rejects_bad_input_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps({"previous": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                run_change_report(path)

    def test_cli_module_rejects_invalid_overlap_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps({"previous": [{"competitor": "Acme"}], "current": [{"competitor": "Acme"}]}),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--fail-on-overlap-below",
                    "1.5",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(2, proc.returncode)
            self.assertIn("must be between 0.0 and 1.0", proc.stderr)

    def test_cli_module_rejects_invalid_change_count_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps({"previous": [{"competitor": "Acme"}], "current": [{"competitor": "Acme"}]}),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--fail-on-change-count-above",
                    "-1",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(2, proc.returncode)
            self.assertIn("--fail-on-change-count-above must be >= 0", proc.stderr)

    def test_cli_module_fail_on_coverage_below_exits_non_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps(
                    {
                        "previous": [
                            {"competitor": "Acme", "pricing": "$10", "positioning": "old"},
                            {"competitor": "Nova", "pricing": "$12", "positioning": "old"},
                        ],
                        "current": [
                            {"competitor": "Acme", "pricing": "$15", "positioning": "new"},
                            {"competitor": "Nova", "pricing": "$18", "positioning": ""},
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
                    "pricing",
                    "--field",
                    "positioning",
                    "--fail-on-coverage-below",
                    "0.8",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(1, proc.returncode)
            output = json.loads(proc.stdout)
            self.assertIn("coverage", output)

    def test_cli_module_fail_on_coverage_below_exits_zero_when_threshold_met(self):
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

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--field",
                    "pricing",
                    "--fail-on-coverage-below",
                    "1.0",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(0, proc.returncode)

    def test_cli_module_rejects_invalid_coverage_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "snapshots.json"
            path.write_text(
                json.dumps({"previous": [{"competitor": "Acme"}], "current": [{"competitor": "Acme"}]}),
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "competitor_radar.cli",
                    str(path),
                    "--fail-on-coverage-below",
                    "-0.1",
                ],
                check=False,
                capture_output=True,
                text=True,
                env={"PYTHONPATH": "src"},
            )

            self.assertEqual(2, proc.returncode)
            self.assertIn("--fail-on-coverage-below must be between 0.0 and 1.0", proc.stderr)


if __name__ == "__main__":
    unittest.main()

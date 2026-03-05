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

    def test_run_change_report_rejects_bad_input_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps({"previous": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                run_change_report(path)


if __name__ == "__main__":
    unittest.main()

"""Public CLI and experiment contracts for the initial scaffold."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from bitgenesis.cli import main
from bitgenesis.simulation import SimulationConfig, initialize


class ScaffoldTests(unittest.TestCase):
    def test_checked_in_experiment_and_override(self):
        config = Path(__file__).resolve().parents[1] / "experiments/v0/empty-world.toml"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["v0", "--config", str(config), "--seed", "7"]), 0)
        self.assertIn("16 x 12 | seed: 7", output.getvalue())
        self.assertIn("Tick: 0 | population: 0", output.getvalue())
        self.assertIn("not implemented yet", output.getvalue())

    def test_invalid_cli_dimensions_and_future_stage_are_rejected(self):
        for arguments in (["v0", "--width", "0"], ["v1"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(arguments)
                self.assertEqual(error.exception.code, 2)

    def test_incompatible_experiment_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.toml"
            path.write_text('schema_version = 1\nrules_version = "v1"\nstage = "v1"\n'
                            'seed = 42\nwidth = 16\nheight = 12\n', encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(["v0", "--config", str(path)])
            self.assertEqual(error.exception.code, 2)

    def test_world_state_is_not_shared_between_runs(self):
        first = initialize(SimulationConfig())
        second = initialize(SimulationConfig())
        first.world.resources.energy_by_position[(0, 0)] = 3
        self.assertEqual(second.world.resources.energy_by_position, {})
        self.assertEqual(second.tick, 0)


if __name__ == "__main__":
    unittest.main()

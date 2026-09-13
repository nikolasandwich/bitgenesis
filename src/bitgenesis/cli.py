"""Minimal CLI with explicit stage and versioned experiment configuration."""

import argparse
from pathlib import Path
import tomllib

from bitgenesis.simulation import RULES_VERSION, SimulationConfig, initialize
from bitgenesis.visualization import render_summary


def load_config(path: Path) -> dict[str, int]:
    with path.open("rb") as stream:
        values = tomllib.load(stream)
    expected = {"schema_version", "rules_version", "stage", "seed", "width", "height"}
    if set(values) != expected:
        raise ValueError(f"Config requires exactly these keys: {', '.join(sorted(expected))}")
    if type(values["schema_version"]) is not int or values["schema_version"] != 1:
        raise ValueError("Unsupported schema_version; expected 1")
    if values["rules_version"] != RULES_VERSION or values["stage"] != "v0":
        raise ValueError(f"Only stage v0 with rules_version {RULES_VERSION} is supported")
    settings = {key: values[key] for key in ("seed", "width", "height")}
    SimulationConfig(**settings)
    return settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BitGenesis artificial-life research scaffold")
    stages = parser.add_subparsers(dest="stage", required=True)
    v0 = stages.add_parser("v0", help="Initialize the V0 scaffold (no time stepping yet)")
    v0.add_argument("--config", type=Path, help="Versioned TOML experiment definition")
    for name in ("seed", "width", "height"):
        v0.add_argument(f"--{name}", type=int, help=f"Override {name}")
    args = parser.parse_args(argv)
    try:
        settings = load_config(args.config) if args.config else {}
        settings.update({name: getattr(args, name) for name in ("seed", "width", "height")
                         if getattr(args, name) is not None})
        config = SimulationConfig(**settings)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(render_summary(initialize(config)))
    return 0

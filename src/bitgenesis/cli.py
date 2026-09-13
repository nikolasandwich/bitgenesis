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
    audit_command = stages.add_parser("audit", help="Read-only consistency audit of a recorded Darwin run")
    audit_command.add_argument("directory", type=Path)
    checkpoint_command = stages.add_parser("checkpoint", help="Advance V0 with periodic recoverable world states")
    checkpoint_command.add_argument("--resume", type=Path, help="Previous state.json to continue")
    checkpoint_command.add_argument("--config", type=Path, help="Darwin config for a new state")
    checkpoint_command.add_argument("--steps", type=int, default=1000, help="Additional ticks to run")
    checkpoint_command.add_argument("--interval", type=int, default=1000, help="Save every N completed ticks")
    checkpoint_command.add_argument("--output", type=Path, required=True, help="New checkpoint directory")
    v0 = stages.add_parser("v0", help="Run the selected V0 rules or preserved scaffold")
    v0.add_argument("--config", type=Path, help="Versioned TOML experiment definition")
    v0.add_argument("--rules", choices=[RULES_VERSION, "v0-darwin-1"],
                    help="Rules version; defaults to scaffold or the config's version")
    v0.add_argument("--steps", type=int, default=1000, help="Darwin run duration (default 1000)")
    v0.add_argument("--output", type=Path, help="New output directory, required for Darwin runs")
    v0.add_argument("--frame-interval", type=int, default=10, help="Replay sampling interval")
    v0.add_argument("--max-frames", type=int, default=1001, help="Maximum stored replay frames (default 1001)")
    for name in ("seed", "width", "height"):
        v0.add_argument(f"--{name}", type=int, help=f"Override {name}")
    args = parser.parse_args(argv)
    try:
        if args.stage == "checkpoint":
            import json
            from bitgenesis.v0.checkpoint import advance
            from bitgenesis.v0.runner import load_config as load_darwin_config
            config = load_darwin_config(args.config) if args.config else None
            print(json.dumps(advance(args.output, args.steps, args.interval, config, args.resume), indent=2))
            return 0
        if args.stage == "audit":
            import json
            from bitgenesis.v0.audit import audit
            print(json.dumps(audit(args.directory), indent=2))
            return 0
        rules = args.rules
        if args.config:
            with args.config.open("rb") as stream:
                configured_rules = tomllib.load(stream).get("rules_version")
            if rules is not None and rules != configured_rules:
                raise ValueError("--rules conflicts with experiment rules_version")
            rules = configured_rules
        if rules == "v0-darwin-1":
            from dataclasses import replace
            from bitgenesis.v0.engine import Config
            from bitgenesis.v0.runner import load_config as load_darwin_config, run
            config = load_darwin_config(args.config) if args.config else Config()
            config = replace(config, **{name: getattr(args, name) for name in ("seed", "width", "height")
                                       if getattr(args, name) is not None})
            if args.output is None:
                raise ValueError("Darwin runs require --output pointing to a new directory")
            summary = run(config, args.steps, args.output, args.frame_interval, args.max_frames)
            print(f"BitGenesis V0 ({rules}) | tick: {summary['tick']} | "
                  f"population: {summary['population']} | births: {summary['births']}")
            print(f"Artifacts: {args.output.resolve()}")
            return 0
        if args.output is not None:
            raise ValueError("Scaffold rules do not write run artifacts; use --rules v0-darwin-1")
        settings = load_config(args.config) if args.config else {}
        settings.update({name: getattr(args, name) for name in ("seed", "width", "height")
                         if getattr(args, name) is not None})
        config = SimulationConfig(**settings)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(render_summary(initialize(config)))
    return 0

"""Read-only artifact checks independent of simulation stepping code."""

from collections import Counter
import csv
import json
from pathlib import Path


def audit(directory):
    try:
        return _audit(directory)
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError(f"Malformed run artifact: {error}") from error


def _audit(directory):
    directory = Path(directory)
    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    metadata = read("metadata.json")
    require(metadata.get("status") == "complete", "Run is not marked complete")
    require(metadata.get("rules_version") == "v0-darwin-1", "Unsupported rules version")
    schema = metadata.get("output_schema_version", 1)
    require(type(schema) is int and schema in (1, 2), "Unsupported output schema")
    config = metadata["config"]
    steps = metadata["completed_steps"]
    require(steps == metadata["requested_steps"], "Incomplete requested tick range")
    with (directory / "metrics.csv").open(encoding="utf-8", newline="") as stream:
        metrics = []
        for row in csv.DictReader(stream):
            metrics.append({key: (None if value == "" else float(value) if key == "mean_genome" else int(value))
                            for key, value in row.items()})
    require(len(metrics) == steps + 1, "Metrics tick count mismatch")
    initial_count = config["initial_population"]
    previous_supply = previous_dissipation = 0
    for tick, row in enumerate(metrics):
        require(row["tick"] == tick, "Metrics ticks are not contiguous")
        require(row["population"] == initial_count + row["births"] - row["deaths"],
                f"Population accounting mismatch at tick {tick}")
        require(row["organism_energy"] + row["food_energy"] + row["dissipated_energy"] == row["supplied_energy"],
                f"Energy accounting mismatch at tick {tick}")
        require(row["supplied_energy"] >= previous_supply and row["dissipated_energy"] >= previous_dissipation,
                f"Cumulative energy decreased at tick {tick}")
        previous_supply, previous_dissipation = row["supplied_energy"], row["dissipated_energy"]
        require(0 <= row["population"] <= config["width"] * config["height"], "Population outside cell bounds")
    records = read("lineage.json")
    by_id = {o["id"]: o for o in records}
    require(len(by_id) == len(records), "Duplicate organism IDs")
    births, deaths, children = Counter(), Counter(), Counter()
    founder_count = 0
    for o in records:
        require(0 <= o["birth_tick"] <= steps, "Birth outside run interval")
        require(0 <= o["genome"] <= 1000, "Genome outside V0 bounds")
        births[o["birth_tick"]] += 1
        if o["death_tick"] is not None:
            require(o["birth_tick"] < o["death_tick"] <= steps, "Invalid death tick")
            require(o["energy"] == 0, "Dead V0 organism retains energy")
            deaths[o["death_tick"]] += 1
        else:
            require(o["energy"] > 0, "Living organism has no energy")
        if o["parent_id"] is None:
            founder_count += 1
            require(o["birth_tick"] == 0 and o["generation"] == 0 and o["founder_id"] == o["id"],
                    "Invalid founder record")
        else:
            parent = by_id.get(o["parent_id"])
            require(parent is not None, "Missing parent record")
            require(parent["birth_tick"] < o["birth_tick"], "Child predates parent activity")
            require(parent["death_tick"] is None or o["birth_tick"] < parent["death_tick"],
                    "Child born after parent death")
            require(o["generation"] == parent["generation"] + 1, "Generation mismatch")
            require(o["founder_id"] == parent["founder_id"], "Founder ancestry mismatch")
            require(abs(o["genome"] - parent["genome"]) <= config["mutation_step"], "Mutation exceeds configured step")
            if config["mutation_probability"] == 0:
                require(o["genome"] == parent["genome"], "Genome changed in no-mutation run")
            children[parent["id"]] += 1
    require(founder_count == initial_count, "Founder population mismatch")
    require(all(o["offspring"] == children[o["id"]] for o in records), "Direct offspring count mismatch")
    total_births = total_deaths = 0
    for row in metrics:
        tick = row["tick"]
        if tick:
            total_births += births[tick]
        total_deaths += deaths[tick]
        require(row["births"] == total_births and row["deaths"] == total_deaths,
                f"Lineage/metrics mismatch at tick {tick}")
    seen_births, seen_deaths = set(), set()
    last_event_tick = 0
    with (directory / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            require(event["tick"] >= last_event_tick, "Lifecycle events are out of tick order")
            last_event_tick = event["tick"]
            o = by_id.get(event["id"])
            require(o is not None, "Event refers to missing organism")
            require(0 <= event["position"] < config["width"] * config["height"], "Event position outside world")
            if event["event"] == "birth":
                require(o["id"] not in seen_births, "Duplicate birth event")
                require(event["energy"] > 0, "Birth event has no energy")
                require((event["tick"], event["parent_id"], event["genome"]) ==
                        (o["birth_tick"], o["parent_id"], o["genome"]), "Birth event/lineage mismatch")
                seen_births.add(o["id"])
            elif event["event"] == "death":
                require(o["id"] in seen_births and o["id"] not in seen_deaths, "Invalid death event ordering")
                require(event["tick"] == o["death_tick"] and event["energy"] == 0
                        and event["position"] == o["position"], "Death event/lineage mismatch")
                seen_deaths.add(o["id"])
            else:
                raise ValueError("Unsupported lifecycle event")
    require(seen_births == set(by_id), "Missing birth events")
    require(seen_deaths == {o["id"] for o in records if o["death_tick"] is not None}, "Missing death events")
    living = [o for o in records if o["death_tick"] is None]
    require(sum(o["energy"] for o in living) == metrics[-1]["organism_energy"], "Final lineage energy mismatch")
    frames = read("frames.json")
    require(bool(frames) and frames[0]["tick"] == 0 and frames[-1]["tick"] == steps, "Replay endpoints missing")
    require([f["tick"] for f in frames] == sorted({f["tick"] for f in frames}), "Replay ticks unordered or duplicated")
    for f in frames:
        require(0 <= f["tick"] <= steps, "Replay tick outside run")
        row = metrics[f["tick"]]
        require(len(f["food"]) == config["width"] * config["height"], "Replay dimensions mismatch")
        require(all(0 <= food <= config["food_capacity"] for food in f["food"]), "Replay food outside bounds")
        require(sum(f["food"]) == row["food_energy"], "Replay/metrics food mismatch")
        require(len(f["organisms"]) == row["population"], "Replay/metrics population mismatch")
        require(len({o[0] for o in f["organisms"]}) == row["population"], "Replay cell collision")
        require(all(0 <= o[0] < len(f["food"]) and 0 <= o[1] <= 1000 for o in f["organisms"]),
                "Replay organism outside bounds")
        if "metrics" in f:
            require(f["metrics"] == row, "Embedded replay metrics mismatch")
    require(sorted(frames[-1]["organisms"]) == sorted([[o["position"], o["genome"], o["founder_id"]] for o in living]),
            "Final replay/lineage mismatch")
    require(read("summary.json") == metrics[-1], "Summary/metrics mismatch")
    return {"status": "verified", "rules_version": metadata["rules_version"], "ticks": steps,
            "organisms_recorded": len(records), "births": total_births, "deaths": total_deaths,
            "final_population": len(living), "replay_frames": len(frames)}

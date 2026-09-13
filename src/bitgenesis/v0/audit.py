"""Read-only artifact checks independent of simulation stepping code."""

from collections import Counter, defaultdict
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
    def read(name, expected_type):
        value = json.loads((directory / name).read_text(encoding="utf-8"))
        if type(value) is not expected_type:
            kind = "object" if expected_type is dict else "array"
            raise ValueError(f"Malformed run artifact {name}: expected JSON {kind}")
        return value
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    metadata = read("metadata.json", dict)
    require(metadata.get("status") == "complete", "Run is not marked complete")
    require(metadata.get("rules_version") == "v0-darwin-1", "Unsupported rules version")
    schema = metadata.get("output_schema_version", 1)
    require(type(schema) is int and schema in (1, 2), "Unsupported output schema")
    config = metadata["config"]
    required_config = {"seed", "width", "height", "initial_population", "initial_energy",
                       "initial_food", "food_capacity", "regrowth_probability", "regrowth_amount",
                       "feeding_rate", "basal_cost", "movement_cost", "birth_threshold",
                       "birth_cost", "mutation_probability", "mutation_step"}
    require(type(config) is dict and set(config) == required_config,
            "metadata.json config must contain the complete V0 configuration keys")
    for name, value in config.items():
        require(type(value) is int, f"metadata.json config {name} must be an integer")
    for name in ("completed_steps", "requested_steps"):
        require(type(metadata[name]) is int and metadata[name] >= 0,
                f"metadata.json {name} must be a nonnegative integer")
    steps = metadata["completed_steps"]
    require(steps == metadata["requested_steps"], "Incomplete requested tick range")
    with (directory / "metrics.csv").open(encoding="utf-8", newline="") as stream:
        metrics = []
        for row in csv.DictReader(stream):
            metrics.append({key: (None if value == "" else float(value) if key == "mean_genome" else int(value))
                            for key, value in row.items()})
    require(len(metrics) == steps + 1, "Metrics tick count mismatch")
    initial_count = config["initial_population"]
    require(metrics[0]["food_energy"] == config["width"] * config["height"] * config["initial_food"],
            "Initial food energy differs from configuration")
    require(metrics[0]["organism_energy"] == initial_count * config["initial_energy"],
            "Initial organism energy differs from configuration")
    previous_supply = previous_dissipation = 0
    for tick, row in enumerate(metrics):
        require(all(row[key] >= 0 for key in ("population", "births", "deaths", "organism_energy",
                                             "food_energy", "supplied_energy", "dissipated_energy")),
                f"Negative metric at tick {tick}")
        require(row["tick"] == tick, "Metrics ticks are not contiguous")
        require(row["population"] == initial_count + row["births"] - row["deaths"],
                f"Population accounting mismatch at tick {tick}")
        require(row["organism_energy"] + row["food_energy"] + row["dissipated_energy"] == row["supplied_energy"],
                f"Energy accounting mismatch at tick {tick}")
        require(row["supplied_energy"] >= previous_supply and row["dissipated_energy"] >= previous_dissipation,
                f"Cumulative energy decreased at tick {tick}")
        previous_supply, previous_dissipation = row["supplied_energy"], row["dissipated_energy"]
        require(0 <= row["population"] <= config["width"] * config["height"], "Population outside cell bounds")
    records = read("lineage.json", list)
    by_id = {o["id"]: o for o in records}
    require(len(by_id) == len(records), "Duplicate organism IDs")
    births, deaths, children = Counter(), Counter(), Counter()
    born_at, died_at = defaultdict(list), defaultdict(list)
    founder_count = 0
    for o in records:
        require(all(type(o[key]) is int and o[key] >= 0 for key in
                    ("id", "founder_id", "generation", "birth_tick", "genome", "position", "energy", "offspring")),
                "Invalid integer organism field")
        require(o["position"] < config["width"] * config["height"], "Lineage position outside world")
        require(0 <= o["birth_tick"] <= steps, "Birth outside run interval")
        require(0 <= o["genome"] <= 1000, "Genome outside V0 bounds")
        births[o["birth_tick"]] += 1
        born_at[o["birth_tick"]].append(o)
        if o["death_tick"] is not None:
            require(o["birth_tick"] < o["death_tick"] <= steps, "Invalid death tick")
            require(o["energy"] == 0, "Dead V0 organism retains energy")
            deaths[o["death_tick"]] += 1
            died_at[o["death_tick"]].append(o)
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
    frames = read("frames.json", list)
    require(bool(frames) and frames[0]["tick"] == 0 and frames[-1]["tick"] == steps, "Replay endpoints missing")
    require([f["tick"] for f in frames] == sorted({f["tick"] for f in frames}), "Replay ticks unordered or duplicated")
    interval = metadata["frame_interval"]
    require(type(interval) is int and interval > 0, "Replay sampling interval must be a positive integer")
    expected_ticks = list(range(0, steps+1, interval))
    if expected_ticks[-1] != steps:
        expected_ticks.append(steps)
    require([f["tick"] for f in frames] == expected_ticks, "Replay sampling schedule differs from metadata")
    frames_by_tick = {f["tick"]: f for f in frames}
    total_births = total_deaths = 0
    live_genomes, live_founders, live_generations = Counter(), Counter(), Counter()
    live_trait_founders = Counter()
    genome_sum = 0
    for row in metrics:
        tick = row["tick"]
        for sign, population in ((1, born_at[tick]), (-1, died_at[tick])):
            for o in population:
                genome_sum += sign * o["genome"]
                pair = (o["genome"], o["founder_id"])
                live_trait_founders[pair] += sign
                if live_trait_founders[pair] == 0:
                    del live_trait_founders[pair]
                for counter, key in ((live_genomes, "genome"), (live_founders, "founder_id"),
                                     (live_generations, "generation")):
                    counter[o[key]] += sign
                    if counter[o[key]] == 0:
                        del counter[o[key]]
        if tick:
            total_births += births[tick]
        total_deaths += deaths[tick]
        require(row["births"] == total_births and row["deaths"] == total_deaths,
                f"Lineage/metrics mismatch at tick {tick}")
        require(row["mean_genome"] == (genome_sum / row["population"] if row["population"] else None),
                f"Trait mean mismatch at tick {tick}")
        require(row["genome_variants"] == len(live_genomes), f"Trait variant count mismatch at tick {tick}")
        require(row["founder_lineages"] == len(live_founders), f"Founder count mismatch at tick {tick}")
        require(row["max_generation"] == max(live_generations, default=None), f"Generation maximum mismatch at tick {tick}")
        if tick in frames_by_tick:
            shown = Counter((o[1], o[2]) for o in frames_by_tick[tick]["organisms"])
            require(shown == live_trait_founders, f"Replay trait/founder pairs differ from lineage at tick {tick}")
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
    require(read("summary.json", dict) == metrics[-1], "Summary/metrics mismatch")
    return {"status": "verified", "rules_version": metadata["rules_version"], "ticks": steps,
            "organisms_recorded": len(records), "births": total_births, "deaths": total_deaths,
            "final_population": len(living), "replay_frames": len(frames)}

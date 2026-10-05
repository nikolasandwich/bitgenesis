# 设计

严格遵循experiments/v4/study-027.md第1–4节。生产select(records)与独立select(records)各返回筛定对象键genotype/mode/seed/exchange/tick/site/identity/root/energy_before（不含结果）；run_probe(case,selection) / verify_probe(case,selection)返回协议record。生产phase(initial)和独立phase(initial)返回units/raw/material。summarize/aggregate固定52选择顺序、四格。helper source_cases返回(genotype,Path)，input_paths(errors)/bindings/read/digest/save仅IO。

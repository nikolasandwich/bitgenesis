# 设计

合同experiments/v4/study-022.md。生产run_case(name)保持旧run_v4_copy_control.run_case case格式，唯一程序初态差异固定。CONFIG、三name顺序同旧。run_probe(case,source_id)返回source_id/status/source/initial/physical；unavailable时后三字段null。source为site/material/energy/program（第32步取实际值），initial为units256/raw256，physical为旧step完整记录加tick1/units/raw/energy/directions/mutation_tickets。status=complete表示探针执行成功，不代表预期材料满足；status=unavailable表示固定来源缺失。

summarize(cases,probes,old_cases)返回cases（三主case.summary的原样列表）、formation_directions（三行dict name/counts四整数）、formed_programs（三行dict name/counts，其中counts为按program字典序排序的program四整数/count整数对象列表）、physical_equivalence（三行dict name/equal布尔）、probes（两行source_id/status/formed_materials排序材料列表）、expectations_met布尔。physical_equivalence比较初始/每步/最终的units仅material/energy、raw、site_ids及final.parents，保留各输入实际值；不比较程序字段。expectations_met为constructed-off persistent10、无原料births0、全部physical_equivalence True、两probe complete且formed_materials分别[1]/[2]。期望false仍可metadata complete。

核验verify_case(case)独立重新构造case并返回summary；verify_probe(probe,case)独立来源提取及物理，返回其摘要；aggregate(cases,probes,old_cases)独立所有统计。helper bindings/read/digest/save；源旧cases直接read data/v4-copy-control/cases.json，已在历史绑定中。

metadata status/planned_cases3/completed_cases/planned_probes2/completed_probes/new_simulation_steps（32每主例+1每complete探针）/new_independent_sources0/artificial_controlTrue/git_commit/time_limit_seconds300/storage_limit_bytes33554432/elapsed_seconds/input_sha256/input_sha256_after/output_sha256（三文件cases/probes/summary）。正式所有案例完成后expectations_met同步summary。异常保留partial；输出目录独占。

# Study027：北向仅能量不足状态的阶段补能探针

## 1 完整固定集合

026全部240案例账本中，选择root0/1、direction3、reason非dissolved、0<energy_interaction<16、target_occupied=False、raw_available>=1的全部行动者。固定52个、每程序26（交换关闭21/开启5），来自random-both；不以处理结果再筛选。选择顺序沿026 records的genotype→mode→exchange→seed，再tick/site。0新环境/初始随机世界，52状态不是52独立来源。

## 2 干预与账本

每状态从保存interaction_units（消解前）及该步前raw起步，原directions/mutation_tickets不变。对照完整运行原heredity.convert，结果units/raw/material必须与原保存本步匹配。处理只把指定source的energy从E补到16，添加16-E外能，其他字段/单元不变。运行原convert一次，包含原消解与全部竞争提案；不再次运行供能/泄漏/连接/交换，也不延时。原construction4/copy1/threshold16/mutation0/16×16规则不变。

每臂检查质量、能量前后与支出：E_after=原阶段总E+added−spent。记录所有单元/原料/提案，处理如影响其他提案亦保留。总104次新形成阶段转换，0新完整世界步，不能混称自然轨迹延续或自主供能。

## 3 输出与核验

scripts/north_energy_inputs.py仅IO/绑定；run_v4_north_energy.py生产，verify_v4_north_energy.py独立核验。生产选择026保存actor账本；核验以verify_v4_north_opportunities.recount逐case独立重建原240案例再筛选。新转换核验用既有字典reconstruct_material(cost5)及独立遗传材料表达封装，不调用新生产phase。

record字段genotype/mode/seed/exchange/tick/site/identity/root/energy_before/added_energy/initial/control/treated。initial为units/raw/directions/mutation_tickets；control与treated各为units/raw/material。energy_before是指定单元原阶段能量。records固定52有序，全字段双路线比较。

summary四格顺序genotype homogeneous/heterogeneous→exchange False/True，各字段genotype/exchange/probes/control_formed/treated_formed/nonzero_treated/added_energy/treated_reasons/total_formed_delta/spent_delta/energy_after_delta/other_reason_changes。前两formed只计指定行动者；treated_reasons含energy/occupied/raw_material/collision/formed五键；total_formed_delta为全部提案形成数处理−对照，other_reason_changes为非指定source提案reason改变总数。逐source报告，保留全部52阴性/反向结果，不做独立样本显著性。

## 4 来源、预算与授权

继承026的389绑定，加026四源/四归档8与本协议/新3脚本4，共401。helper source_cases复用026顺序；initialinventory在验证前保留可读hash/errors。独占data/v4-study-027，干净提交，300秒/32MiB，最终写入后复查预算；异常保留进度/前后hash，不覆盖旧数据。

metadata planned_probes52/completed_probes/new_phase_transitions（最终104）/new_full_world_steps0/new_environment_sources0/reused_environment_sources20/new_independent_initial_worlds0，加status/git_commit/elapsed_seconds/time_limit_seconds300/storage_limit_bytes33554432/input_paths/input_sha256/input_sha256_after/output_sha256。四根metadata/records/summary/independent-verification完整逐字节归档。独立proof绑定运行核验器hash与全部输出/输入，失败证据保留。

用户持续自主研究授权下intentional fast-track；先反例后实现、全套回归、独立审查及报告状态提交推送。只检验筛定集合的局部补能充分性，不推广到另外296个合并受阻energy事件，不改变原生命/持续10步标准。

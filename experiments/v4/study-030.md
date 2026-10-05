# Study030：固定出生位置的完整供能时序

## 1 队列与边界

只读028全部52分支及029对应能量记录，原顺序、原终点32不变。每条从birth_tick+1至32，共996个位置时步；其中268步开始时原child存活。包含死亡后票，但不能让死亡单元复活或将别的身份摄取算给原child。0新模拟/物理干预/环境/初始世界。20旧环境筛选来源，实际11seed/26原案例臂。

问题：完整剩余窗口有无供能、第一次发生在死前/死亡步/死后、哪些票因程序对应状态不同而落入不同生命周期。只作保存时序核查，不将死后提议当可实现收益，不延长窗口。

## 2 精确记录

每record键selection（原九键）,child_identity,child_site,birth_tick,death_tick,rows,totals,first_proposed_tick,first_proposed_phase,first_after_death_tick。后三项无相应proposed>0则null。phase为before_death（tick<death）、death（相等）、after_death（大于）。

row键tick,phase,identity_before,identity_after,proposed,site_accepted,child_accepted,other_accepted,rejected。身份来自该site步前/后状态，None为空位；child_accepted仅identity_before==child时等于site_accepted，否则0；other_accepted为其余实际摄取。输入发生在消解前，所以死亡步也先检查原身份。proposed必须原票0或8，site_accepted+rejected=proposed；不能将空位的拒绝票当摄取。

totals键steps,proposal_events,before_death_events,death_events,after_death_events,proposed,before_death_proposed,death_proposed,after_death_proposed,site_accepted,child_accepted,other_accepted,rejected。events计proposed>0，三phase求和守恒；child_accepted总量必须与对应029 totals.accepted相同。身份在birth到death步开始时仍为child，death以后不是child；固定child_site不移动。逐row比对029在生前/死亡步的proposed/accepted，死后不能混入该生命周期。

## 3 两路线、汇总与配对

scripts/analyze_v4_feed_timing.py analyze_branch(branch,energy)→record，summarize(records)→dict(cells,pairs)，main。生产从保存输入/site_ids直接提取。

scripts/verify_v4_feed_timing.py recount(branch,energy)→record，aggregate(records)→summary，main。先调用旧verify_v4_child_energy.recount(branch)独立重放全部后续物理/身份，与对应energy全字段比对，然后独立构建时序记录，不调用新生产。仅共享旧核验和IO。

cells按genotype→exchange四格，键genotype,exchange,n,totals（上述13指标合计）,no_proposal,first_before_death,first_at_death,first_after_death,any_after_death,any_child_accepted,any_other_accepted（七项记录计数）。四项首次分类no/before/at/after合计n。

pairs按均一原顺序26项，每项selection（除genotype八键）,homogeneous_index,heterogeneous_index,delta（13totals异质−均一）,phase_shift_ticks（同一proposed>0但phase不同的tick升序列表）。必须对应child_site、birth_tick、完整tick/proposed票序列相同；配对不可重复/遗漏。供能时序的总提议相同，但其生命周期分类或实际接受可以不同。保留全部零/反向差，不作独立样本显著性。

## 4 证据与预算

scripts/feed_timing_inputs.py只提供read/save/digest/source_cases（02852Paths）/input_paths(errors)/bindings；继承029的479绑定，加029四根/四归档8，本协议与三新脚本4，共491。验证029proof/status/996与268/26pairs、479前后绑定、三输出hash及四归档逐字节一致；028完整case/tar校验由旧绑定继承。

独占data/v4-study-030，干净提交，300秒/32MiB，最终写入后复查。metadata含status/planned_branches52/completed_branches/saved_world_steps996/site_steps996/live_start_steps268/new_full_world_steps0/new_phase_transitions0/new_environment_sources0/reused_environment_sources20/selected_environment_sources11/new_independent_initial_worlds0/git_commit/elapsed_seconds/time_limit_seconds300/storage_limit_bytes33554432/input_paths/input_sha256/input_sha256_after/output_sha256。初始inventory先于严格校验，metadata不可读回退归档；错误保留前后hash/读错/进度。可保留input_inventory_errors/input_read_errors_before成功空dict。

proof核验52/996位置步、26pair、491输入与三输出，核验器自身hash、预算和前后绑定；独占写入，失败保留。metadata/records/summary/independent-verification四根JSON逐字节归档，原轨迹不复制。持续研究授权intentional fast-track；先TDD及审查、干净提交再正式全量，不做工程全52dryrun。独立作者审查不可用如实inline fallback。

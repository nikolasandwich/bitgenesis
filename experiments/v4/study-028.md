# Study028：一次补能形成后的固定窗口延续

## 1 固定问题、队列与预算

接续027全部52条记录，顺序完全不变；不按未来结果选择。沿各自原来源方向、供能和突变票，从干预tick的treated最终态继续tick+1到32，不再补能，不延长窗口。共996个新完整世界步、0新形成阶段重做、0新环境或初始随机世界。筛选涉及20旧环境票，入选实际11seed/26来源案例臂，不作52独立样本显著性检验。原source原轨迹为对照，无需重新生产对照。

独占data/v4-study-028，干净提交启动，600秒/128MiB；逐分支保存，异常保留进度、实际完成步数、输入/输出前后hash和逐文件读取错误，不覆盖旧输出。

## 2 身份、状态和物理

沿用源初态和干预前全部身份。生产Observer重放原tick<干预tick的事件（非物理运行），然后accept包含tick与027 treated units/raw/material的阶段事件，按提案顺序分配新身份。指定source北向新生身份记injected_child；不得沿用原轨迹未来身份，其他同时新生也按本分支顺序重新分配。独立核验用plain parents/site_ids数组按消解/形成重建，不使用Observer。

branch.initial字段tick,units,raw,site_ids,parents,observation,injected_child；是027处理阶段终态。rows仅保存后续完整物理步，各含tick/site_ids/physical/observation；final字段tick32/units/raw/site_ids/parents。branch另有selection（027九身份字段）,added_energy（历史一次性外能）,copy_parents,metrics,control_metrics,delta,child_fate。

生产使用原hereditary_growing.step；独立使用exchange_branch_audit.physical_step，逐字段比较全部物理/原票/身份/组件。不修改模型。每步能量守恒、质量7；从branch.initial到final的能量账本仅initial_energy+后续imported−后续spent，不重复计入027外能。新供能必须来自source保存的proposed，不能使用原accepted。

## 3 观察指标和对照

构造仅供观察器读取的32行：源tick<干预tick保存行、干预tick的initial units/ids/observation投影、后续rows。该干预行不是完整物理步，不伪造其供能或支出。初态模板仍原source.initial；用原analyze / 独立recount求四类完整32步copy_parents，不改变标准。

metrics/control_metrics均10个整数键：births,deaths（仅tick+1..32，排除当步新增形成），living,final_energy（第32步全世界），imported,spent（仅后续完整步），genetic_ever,genetic_persistent10,longest_genetic,material_ever（原完整1..32观察窗）。delta为逐键treated−control。对照重新从原保存rows及原copy_parents提取，不运行新对照世界。births/deaths/供能差不包含干预当步，外能added_energy另列。

child_fate字段：identity,birth_tick,death_tick（观察内首次消解tick，否则null/right-censored）,alive_final(bool),direct_offspring,descendants_born（所有世代、不含自身）,lineage_living_final（包含自身）,observed_alive_finals（从形成tick到死前或32的final存活次数）。派生祖链仅属于该分支；不跨分支比较数值身份。报告全部死亡及右删失情况。

records.json每项为selection,added_energy,metrics,control_metrics,delta,child_fate（case其余大数组不重复）。summary.json为四格list，genotype→exchange，字段genotype,exchange,n,totals,control_totals,delta_totals,positive,negative,tie,child_alive_final,child_reproduced,lineage_alive_final；totals等前三字典为10指标合计，positive/negative/tie为各指标差方向计数。每格n21/5；子命运三个计数分别alive_final/direct_offspring>0/lineage_living_final>0。不以末态个体存活替代遗传双副本，也不把延续改善称自主供能。

## 4 来源、实现与核验

新增scripts/energy_continuation_inputs.py仅IO：继承027的401绑定、加027四根/四归档8及本协议/三新脚本4，共413。校验027完整proof、401前后绑定和四归档一致。source_cases复用027helper提供240源路径；probes从027records读取。初始inventory在严格验证前记录，metadata缺失时回退已追踪归档。

生产scripts/run_v4_energy_continuation.py：run_branch(source,probe)、record(branch)、summarize(records)、main。核验scripts/verify_v4_energy_continuation.py：verify_branch(source,probe)独立构建相同branch；record(branch)、aggregate(records)、main。不调用/读取新生产实现。核验先以旧027 verify_probe检查每个选中源/阶段记录，再独立重放后续996步；沿用已绑定026/027全队列筛选证明。两条新路线完整分支及汇总必须相等。

cases/branch-000.json至branch-051.json保存完整分支。metadata含status/planned_branches52/completed_branches/new_full_world_steps（最终996）/new_phase_transitions0/new_environment_sources0/reused_environment_sources20/selected_environment_sources11/new_independent_initial_worlds0/git_commit/elapsed_seconds/time_limit_seconds600/storage_limit_bytes134217728/input_paths/input_sha256/input_sha256_after/output_sha256。proof记录413输入、全部55输出hash（52cases+records/summary/metadata）、核验器hash及前后绑定/耗时/预算。最终写入后再查预算。根四JSON逐字节归档，52case压缩归档并在空目录实际恢复逐文件hash核验。

持续自主研究授权下intentional fast-track；先反例测试、工程审查、干净提交，再唯一一次正式全队列运行。工程最多少量固定fixture，不做全52处理dry-run。独立作者审查不可用时明确inline fallback。后续研究由结果决定，不预设阳性。

# Study029：新增单元完整生命周期能量账本

## 1 固定队列与问题

只读028全部52分支，顺序不变。每分支追踪initial.injected_child，从形成后能量5的初态至已记录消解步，包含死亡步；不按接受量或存活长度筛选。总268个单元转换（64/26/129/49），来自已核验996世界步，不新增模拟/环境/初始世界。筛选复用20旧环境票，实际11seed/26来源案例臂。

比较同seed/exchange/tick/site/identity/root/energy_before的26对均一与异质状态；两个程序各21关闭/5开启。账目分解只能解释实际收支，不把事件关联当必要因果。0新物理干预、不补能、不延时。

## 2 逐步定义与账本

生产从028保存physical提取；独立核验从各branch.initial以旧exchange_branch_audit.physical_step重放全部996保存步，逐字段比较physical，plain IDs/parents验证身份和死亡，不调用新生产分析。每步只在开始时该child仍活着才记录；该单元不移动，child_site由initial.site_ids定位并逐步校验。消解后不追踪后来同site的其他身份。

每记录selection（原027九键）、child_identity、child_site、birth_tick、death_tick、initial_energy、rows、totals。

row精确键tick,energy_before,proposed,accepted,leakage,bond_cost,exchange_in,exchange_out,energy_interaction,formation_spent,offspring_energy,energy_after,dissolved。proposed/accepted/leakage为该site输入；bond_cost是当步实际连接incident数×原成本1，不能用同材料邻居数代替；exchange_in/out为实际传输。energy_interaction为形成前保存能量。

formation_spent为该child作为parent成功形成时construction4+copy1；offspring_energy是这些新生分走的能量。父子分配不应全记成耗散。energy_after为该身份final能量，消解后记0并dissolved=True；同site若再出生不能计为原child存活。每步energy_interaction=before+accepted−leakage−bond_cost+in−out；after=interaction−formation_spent−offspring_energy。消解步interaction为0。实际028无child再形成，但用工程反例检验形成成本/子能量分离。

totals精确键steps,proposed,accepted,leakage,bond_cost,exchange_in,exchange_out,formation_spent,offspring_energy,final_energy。steps=len(rows)=death_tick−birth_tick；其余累加相应row项，final_energy仅末row.energy_after。检查initial5+accepted−leakage−bond_cost+in−out−formation_spent−offspring_energy=final0。52全死亡、总268步必须成立。零接受及零交换记录完整保留。

## 3 汇总、配对与接口

summary为dict(cells,pairs)。cells顺序homogeneous/heterogeneous→exchange False/True；各键genotype,exchange,n,totals（上述十指标合计）,zero_accepted,received_exchange,paid_bond（分别totals.accepted==0/exchange_in>0/bond_cost>0的记录数）。pairs按均一记录顺序26项，每项selection（除genotype八键）、homogeneous_index,heterogeneous_index,delta（十指标异质−均一）。必须完整唯一对应，不作独立样本显著性。

scripts/analyze_v4_child_energy.py analyze_branch(branch)→record；summarize(records)→summary；main。scripts/verify_v4_child_energy.py recount(branch)→record；aggregate(records)→summary；main；新计算路线互不读取实现。scripts/child_energy_inputs.py仅IO，source_cases()按序返回52个Path；read/save/digest/input_paths(errors)/bindings。

## 4 绑定、预算、保留

继承028运行的413绑定，加028源四根/对应归档四根8，52cases，cases.tar.gz及archive-verification.json两归档2，本协议和三新脚本4，共479。验证028proof/status/413前后hash/55输出hash、四根逐字节归档，52case与已实际恢复manifest逐项一致且tar的52成员内容一致。

独占data/v4-study-029，干净提交，300秒/32MiB；metadata记录status/planned_branches52/completed_branches/saved_world_steps996/child_steps（最终268）/new_full_world_steps0/new_phase_transitions0/new_environment_sources0/reused_environment_sources20/selected_environment_sources11/new_independent_initial_worlds0/git_commit/elapsed_seconds/time_limit_seconds300/storage_limit_bytes33554432/input_paths/input_sha256/input_sha256_after/output_sha256。初始inventory在严格校验前记录，根metadata缺失回退追踪归档，异常保留前后实际hash与逐文件错误。最终写入后再查预算。

proof绑定479输入、metadata/records/summary三输出及自身hash，独立复算全部996保存步与268单元步、完整26配对；独占写入，异常保留，不覆盖既有结果。根四JSON完整逐字节归档，不重复复制028原始轨迹。用户持续授权intentional fast-track；先RED反例/实现/回归/审查/提交，再正式全量只读分析；工程不做完整全队列dryrun，独立作者审查不可用时准确inline fallback。

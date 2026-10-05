# Study033：逐位置材料守恒与北向目标

## 1 问题、来源与不变量

只读026已绑定的240保存案例（019均一120、023异质方向40、025异质供能/双随机80），每条初态及32末态，共7920快照、2027520位置检查。顺序genotype homogeneous/heterogeneous→mode random-direction/random-feed/random-both→exchange False/True→seed120000..120019。不新增实验模拟、环境或初始世界。

检验每site的raw+int(unit非空)是否恒等初始值，所有偏差保留violations，不只检查总质量。初始支持集预期[85,86,101,102,117,118,204]，各1；其余249位置0。机制证明来自driven无位置变化、同site死亡单位转raw+1、形成目标raw−1且占据+1，亲本位置占据不变；程序和能量变化不迁移材料。该结论限现引擎和初始支持，不否认支持集内再生/复制，不宣称生命不可能。

北向事件沿026完整行动者记录，选direction3且reason非dissolved（存活提案），另保留北向票及消解数。all全部root，target仅root0/1。目标类别严格按顺序：初始该位置库存0且当前raw_available0且不占据为no_initial_material；初始库存1且当前占据且raw0为occupied；初始库存1且不占据且raw1为available；其余other，全部保留。不把执行reason raw_material当唯一因果；每类还记录能量阈值和实际reason。

## 2 输出及独立核验

生产scripts/analyze_v4_material_support.py analyze_case(case,actors)→record，actors是026对应记录；直接逐快照查局部库存，并从旧actors提取分类。独立scripts/verify_v4_material_support.py analyze_case(case,actors)→同record：先调用旧verify_v4_north_opportunities.recount(case,genotype)完整字典物理重放，要求与actors相等；独立构造局部库存/分类，不读新生产实现。

record键genotype,mode,exchange,seed,support,checked_snapshots=33,checked_sites=8448,violations,north_tickets,north_dissolved,events。violations每项tick,site,expected,actual，按tick/site序；support为初始库存>0的site列表。north_tickets/north_dissolved各dict(all,target)。events按tick/source site序，每项tick,site,identity,root,target,initial_stock,raw_available,target_occupied,category,energy_ready(bool energy_interaction>=16),reason；只存存活北向。全保存events含零项，不抽样。校验case与actors身份和32列表匹配，固定初态256位置；遇输入损坏拒绝并留证，局部库存偏差本身保留不静默丢弃。

summarize(records)→12格list，顺序同genotype/mode/exchange；每格genotype,mode,exchange,n=20,checked_snapshots,checked_sites,violation_count,scopes。scopes为all/target，每scope含north_tickets,north_dissolved,north_proposals,categories；categories含no_initial_material,occupied,available,other，每项n,energy_ready,reasons（energy,occupied,raw_material,collision,formed全五键int含0）。完整240有序案例才汇总，事件/计数严格类型、非负、类别/原因/schema校验。不能按新结果筛选。

## 3 绑定与预算

父helper scripts/material_support_inputs.py复用north_opportunity_inputs.source_cases/read/save/digest，继承026的389绑定，加026四根/四归档8+本协议/三新脚本4，共401。input_paths(errors)/bindings验证026 complete240/7680、proof verified389、前后输入、三输出hash与四归档字节。只有IO共享，无新科学计算共享。

独占data/v4-study-033，clean launch；300秒/64MiB，逐案例保存records.json及进度，最终写后预算检查。metadata固定planned_cases240,completed_cases,saved_steps(32*n),checked_snapshots(33*n),checked_sites(8448*n),new_simulation_steps0,new_environment_sources0,reused_environment_sources20,new_independent_initial_worlds0,time_limit_seconds300,storage_limit_bytes67108864，另status/git_commit/elapsed_seconds/input_paths/input_sha256/input_sha256_after/output_sha256和可选成功空input_inventory_errors/input_read_errors_before。proof核验401输入、240案例/7680保存步、7920快照/2027520位置、全records/summary、三个输出及自身hash、前后绑定/独占/预算与失败留证。

两新作者独立实现，先TDD与少量fixture（最多各一个真实案例）验证，不在工程期全240预跑；干净提交正式一次。四根JSON完整逐字节归档。持续授权intentional fast-track；第三审查任务不可用则如实inline fallback，不称独立作者审查。

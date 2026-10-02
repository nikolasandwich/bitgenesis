# 设计

协议为docs/design/v4-structure-copy-control.zh-CN.md。

scripts/run_v4_copy_control.py提供run_case(name)，固定顺序names=('constructed-off','constructed-on','no-raw-off')。返回case字典：name/exchange/raw_tokens、config、initial、rows、final、copy_parents、summary。config为width/height/capacity/leak/bond_cost/threshold/construction_cost/copy_cost/mutation_per_thousand，数值按协议；exchange另列。

initial含tick0、units、raw、site_ids、observation(final)。rows为32行tick/site_ids/physical/observation(final)，physical严格采用exchange_branch_audit.physical_step返回格式（原native step账本加tick/units/raw/energy/directions/mutation_tickets），程序和票保存JSON数组。final含tick32、units、raw、site_ids、parents；parents由Observer的individuals提取，初始身份按占据格点顺序0/1/2，目标父组件0。copy_parents为017analyze(initial,rows,final)完整输出（唯一合格组件0）。

summary为name/exchange/raw_tokens/steps32/births/deaths/initial_energy/final_energy/imported/spent/initial_mass/final_mass/genetic_counts(32整数)/episodes(双端包含)/longest/persistent10(bool)。母程序与身份可由完整rows/final复算，不只保留这个汇总。

main在干净提交下独占data/v4-copy-control，metadata/cases/summary JSON逐案例保存。metadata含status/planned_cases3/completed_cases/new_simulation_steps(正式完成后96)/new_independent_sources0/artificial_controlTrue/git_commit/input_sha256/input_sha256_after/output_sha256(cases和summary)/elapsed_seconds/time_limit_seconds60/storage_limit_bytes33554432。bindings涵盖src/bitgenesis/v4全部.py（明确库存）、017analyze/verify/structure_copy_inputs/horizon_fate_inputs、本协议与两新脚本，按相对路径排序并SHA256。失败留下已完成案例及原因，不复用目录。

scripts/verify_v4_copy_control.py不导入run脚本，独立case验证函数verify_case(case)返回自身summary。从另写常量重建三初态、32输入票与config，physical_step重建全部物理；自行更新身份和parents，structure_audit.reconstruct重建分区，017recount核对全部copies。main核对元数据、全部输入前后哈希（独立列清单）、三cases严格顺序、summary及结果文件哈希，独占写independent-verification.json；失败保留verification-failure.json。新增物理独立性使用已有dictionary审计链，空间匹配独立性复用017两算法，明确依赖范围。

测试包括输入固定（含所有空位置票）、形成/能量/质量/分区双路线、原料0负对照、被篡改输入/身份/匹配被拒绝。正式队列前可执行工程测试；这些确定性重复不成为独立研究样本。期望阳性未满足应使测试/预期判据失败，记录原参数和失败，不静默调参。

metadata完成时增加expectations_met：constructed-off的persistent10为true且no-raw-off的births为0；仅在三例全部运行后判断，未达预期不提前截断。status描述执行完成或异常，expectations_met描述预期实现与否，两者分开。

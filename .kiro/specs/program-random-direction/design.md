# 设计

合同experiments/v4/study-023.md。run_case(source)接收019 random-direction case，只用其seed/exchange与输入票，返回原019 case schema（包括summary字段完全同旧019）。程序初态A/B固定。CONFIG/32步同旧。verify_case(case,source)独立重建并返回case.summary。

metrics(case)返回下列13个原生整数：genetic_persistent10,genetic_ever,material_persistent10,material_ever,longest_genetic,births,deaths,living,imported,spent,final_energy,nonzero_births,north_births。前4为0/1，material从copy_parents[0].series.descendant_material与longest计算；后两量从全formed提案material!=0及direction==3计数（包括全部祖源，但孤立单位原料不可达）。

pair_record(case,source)返回seed/exchange/homogeneous/heterogeneous/delta，后三为指标字典，delta=新−旧。summarize(records)要求固定40完整唯一seed×False/True，返回cells与contrasts：cells4行按genotype('homogeneous','heterogeneous')再exchange(False,True)，行genotype/exchange/n20/totals（指标整数和）/means（str(Fraction)）；contrasts2行exchange/n20/mean_delta/positive/negative/tie，后4为每指标字典（均差精确Fraction字符串、其他为来源计数）。核验独立metrics/pair_record/aggregate同schema。

helper source_cases() yield Path按seed再False/True；路径固定data/v4-study-019/cases/seed-{s}-random-direction-exchange-{e}.json。新输出case同名，metadata字段status/planned_cases40/completed_cases/new_simulation_steps/new_environment_sources0/reused_environment_sources20/new_independent_initial_worlds0/artificial_initial_stateTrue/git_commit/elapsed_seconds/time_limit_seconds600/storage_limit_bytes134217728/input_sha256/input_sha256_after/output_sha256（cases/*与results/summary）。results.json是上述配对记录列表；summary.json为cells/contrasts，proof核对全40/1280及229输入、运行核验器hash。异常独占失败保留，完整列表不足不得聚合。

# 设计

合同experiments/v4/study-019.md。三新工具scripts/copy_ablation_inputs.py、run_v4_copy_ablation.py、verify_v4_copy_ablation.py。helper仅用于绑定/read/digest，复用run_v4_copy_control.bindings的45输入，再加入原控制四根JSON/四归档、019协议和三新脚本=57；核验原proof核验器hash/输出hash/前后输入与归档字节。不得共享新科学算法或随机票函数。

## 案例与接口

顺序GRID=product(range(120000,120020),('random-direction','random-feed','random-both'),(False,True))，键seed/mode/exchange。run_case(seed,mode,exchange)返回case。producer.tapes(seed)生成32行directions(256整数)/feed_sites(4独一整数)，供测试复算；verify另写随机化，不能调用producer。

case沿旧受控格式，但name/raw_tokens由seed/mode替代：seed/mode/exchange/config/initial/rows/final/copy_parents/summary。config和initial严格同旧constructed（四原料、质量7）；rows32与physical字段模式同旧工具；final及copy_parents同。summary固定seed/mode/exchange/steps32/births/deaths/living/initial_energy/final_energy/imported/rejected_import/spent/proposed1024/initial_mass/final_mass/genetic_counts(32)/episodes/longest/persistent10/ever。所有数值原生int，开关及事件bool；原程序绝对方向不随随机方向改动。

生产summarize(summaries)与核验独立aggregate(summaries)生成：cells6行mode/exchange/n20/successes/ever_count/success_fraction/ever_fraction/mean_longest/mean_births/mean_deaths/mean_living/mean_imported/mean_rejected_import/mean_spent，全部fraction和mean用str(Fraction)。cells顺序mode三类，exchange False/True。pairs60行seed/mode/off/on/difference（bool/bool/int，主要成功差开−关）；groups3行mode/n20/on_only/off_only/both/neither/mean_difference（精确Fraction）。所有120案例必须完整、唯一且严格类型，失败不当0。

## 保存与核验

data/v4-study-019/cases/seed-{seed}-{mode}-exchange-{str(exchange).lower()}.json保存全部case；每完成一次更新results.json的120摘要逐渐增长。summary.json只在全部成功后产生。

metadata沿受控框架：status/planned_cases120/completed_cases/new_simulation_steps32*completed/new_independent_initial_worlds0/new_environment_sources20/artificial_initial_stateTrue/git_commit/input_sha256/input_sha256_after/output_sha256（相对文件名cases/*.json及results.json/summary.json）/elapsed_seconds/time_limit_seconds600/storage_limit_bytes268435456。干净启动、独占目录、每例校验输入及预算、失败部分保留。不把input来源字段命名new_independent_sources以免和旧自然样本混淆。

verify_case(case)返回独立summary，主程序逐案例核对期望文件库存与输出hash、完整120/3840、完整统计及两个旧确定性参照仍绑定；新proof独占写independent-verification.json，失败写verification-failure.json。范围为完整环境票/物理/祖源/分区/匹配与统计；独立性复用已存在dictionary审计链和017两匹配算法。

## 测试与保全

真实少量fixture可使用公共run_case（不读另一作者实现），篡改随机方向/供能数/身份/摘要必须拒绝；统计反例需包含开/关单侧成功、双成功/双失败、缺失重复及错误类型。父代理运行一次完整套件，双方仅各自专项。工程测试的确定性重复与正式3840步区分。

报告阶段将cases全部文件压缩tar.gz并保存逐文件size/SHA256清单，空临时目录解压后逐项一致，压缩文件SHA256归档。元数据/results/summary/independent-verification直接逐字节复制进docs/research/results；不修改正在绑定的科学代码或协议。

metadata增加python_version（platform.python_version），独立凭据记录核验运行时版本；实际输入票仍完整保存并独立重算，不以版本字符串替代重放。

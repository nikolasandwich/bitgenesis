# Study032：孤立能量模型的最终吸收与等待时间

## 1 问题和范围

承接031同一解析模型：单位置逐步独立名义p=1/64供8、否则0，先输入后泄漏1，无连接或交换。能量0为死亡吸收，>=16为首次能量达标吸收；活态1..15。固定求全部15初始能量的最终hit/dead概率和到任一吸收的平均步数，主结论初能5。不把达标当形成或复制，不推真实世界因果、不调参，不新增模拟/环境/初始世界，不把52相关状态作独立样本。

每15步全无供能概率q^15>0，从任一活态均已死亡或此前达标，故P(T>15n)<=(1-q^15)^n，几乎必然吸收且E[T]<=15/q^15。此为解析证明，不用数值截断替代最终值。

## 2 两种精确求解与接口

生产scripts/analyze_v4_energy_absorption.py：15未知数的Fraction Gauss-Jordan；方程64h(e)-63h(e-1)-h(e+7)=0，h(0)=0,h(>=16)=1；64t(e)-63t(e-1)-t(e+7)=64，t(0)=t(>=16)=0。独立scripts/verify_v4_energy_absorption.py：边界递推h(e+7)=64h(e)-63h(e-1)、t(e+7)=64t(e)-63t(e-1)-64，以e1..7为未知仿射表达式，递推e8..22，使用e16..22的7个边界条件。用整数Bareiss行列式及Cramer法解7x7，不读取/调用新生产算法；精确有理运算，无科学浮点。

两脚本solve_states()→15项list，energy升序1..15，每项energy整数，hit/dead/mean_steps规范str(Fraction)，dead=1-hit。必须验证每能量hit/dead在[0,1]、mean_steps>0、概率守恒及原15组Bellman方程。工程只测试小矩阵有理解/行交换/奇异反例、边界递推合成fixture及mock solve_states的衔接管线；正式15态只从干净提交运行一次生产和独立核验。

build(prior_records)→(records,summary)。prior_records为031 records，完整33曲线和52cohort由输入绑定保障。records={states,finite_checks}。每finite_checks按horizon0..32：horizon,hit_reconstructed,mean_steps_reconstructed,additional_hit,remaining_mean_steps。令a_t(e)为031未吸收活态分布，H_t为其hit，S_t为surviving：additional_hit=sum a_t(e)h(e)，remaining_mean_steps=sum a_t(e)t(e)，hit_reconstructed=H_t+additional_hit必须等于h(5)，mean_steps_reconstructed=sum(k=0..t-1)S_k+remaining_mean_steps必须等于t(5)。全部输出概率/时间为规范分数字符串。

summary精确键initial_energy=5,eventual_hit,eventual_dead,mean_absorption_steps,at_32_hit,additional_hit_after_32,remaining_mean_steps_after_32,at_32_surviving；后七字段字符串。所有33衔接成立，额外hit不得超过未吸收质量，剩余平均步数是无条件尾部贡献，不是幸存条件期望。

## 3 输入、预算和证据

父实现scripts/energy_absorption_inputs.py仅IO：继承031的503绑定，加031四根/四归档8与本协议/三新脚本4，共515；接口read/save/digest/input_paths(errors)/bindings。验证031 complete33、52队列、proof verified503/33/52/4、前后hash、三输出hash、自身verifierhash与四归档逐字节相同。路径清单先保存，坏根metadata回退归档，失败保留可读hash及错误。

data/v4-study-032独占目录，clean launch，60秒/8MiB，最终写入后再查预算，异常保留，不覆盖旧结果。metadata固定status、planned_states15、completed_states、finite_horizons33、initial_energy5、new_full_world_steps0、new_phase_transitions0、new_environment_sources0、new_independent_initial_worlds0、time_limit_seconds60、storage_limit_bytes8388608；另git_commit、elapsed_seconds、input_paths、input_sha256、input_sha256_after、output_sha256，可加成功空input_inventory_errors/input_read_errors_before。

proof核验515输入、15态、33衔接和summary、metadata/records/summary三输出、自身脚本hash、前后输入，独占写入/最终预算/失败证据。四根JSON完整逐字节归档。运行前TDD和审查，持续授权intentional fast-track；若第三作者审查不可用，记录inline fallback，不冒称独立作者审查。

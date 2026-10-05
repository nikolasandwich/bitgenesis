# Study031：有限时域孤立单元的精确能量可达性

## 1 固定解析问题与范围

这是原名义输入机制的解析参照，不新增世界或改变引擎。单固定位置每步从256位置均匀抽4个，因此名义p=4/256=1/64；解析假设不同步独立Bernoulli票，不把已固定20种子的经验频数当p，不假定不同位置/配对分支相互独立。

初能5，先输入8（概率1/64）或0（63/64），再泄漏1；无连接、无交换。不复活：能量到0进入永久死亡吸收态；首次形成前能量>=16进入永久达标吸收态，尚未达标的活态仅1..15。转移e→e+8b−1；到达阈值先记录hit，不继续计算实际形成。阈值前最大新能量22<64，容量不截断。达到16只是能量条件，不含方向、空位、原料、组件复制或持续10步标准；有交换增益的世界不能套用此孤立参照作为普遍上界。

预先固定全部horizon0..32共33点，重点标记030全52状态的剩余32−birth_tick（10..26）；不以结果挑时域。0新实验模拟、环境、初始世界。解析事件概率不是这些固定轨迹的实测发生率。

## 2 两条精确路线与输出

生产用整数路径权重前向递推，每步无票×63、有票×1，总分母64^t，吸收态每步×64；仅序列化时用Fraction约分。独立核验用终态事件指示函数的反向递归/动态规划、Fraction权重63/64与1/64，分别求hit/dead和每个活能量终态；不读取/调用新生产实现。两路线全部33×15分布及累计/首次概率完全相等。禁止浮点参与科学计算。

每curve row键horizon,alive（15元素list，对应1..15概率字符串）,first_hit,first_death,hit,dead,surviving。所有概率为str(Fraction)，即0/1等标准字符串；t0只有alive[4]=1、surviving1，其余0。first_hit/first_death是累计差，t0为0。每行hit+dead+surviving=1，surviving=sum(alive)，吸收累计不降且概率非负。

records.json为dict(curve,cohort)。cohort沿030原52记录顺序，每项selection（九键）,horizon,hit,dead,surviving；horizon=32−birth_tick，概率引用curve同点。summary.json为四格list，genotype→exchange；每格genotype,exchange,n,expected_hits,mean_hit,mean_dead,mean_surviving。expected_hits是该名义参照下对状态加权概率之和（线性期望，无需独立），不是真实世界预测成功数；均值分母为状态数21/5。不得据此计算独立二项零成功概率或显著性。

scripts/analyze_v4_energy_probability.py curve(max_horizon=32)→list；build(timing_records)→(records,summary)；main。scripts/verify_v4_energy_probability.py curve(max_horizon=32)→list；build(timing_records)→(records,summary)；main。输入timing_records为030全部52，必须保留完整九键/顺序/52队列，出生tick与selection.tick一致。新算法独立，仅共享IO及旧选择验证允许。工程只检查短时域闭式式子/少量fixture，不预跑全33正式曲线。

## 3 绑定、预算与保留

scripts/energy_probability_inputs.py仅IO：继承030的491绑定，加030四根/四归档8与本协议/三新脚本4，共503。read/save/digest/input_paths(errors)/bindings；030proof/status/491前后绑定/三输出hash与四归档一致。初始inventory严格验证前保存，根metadata不可读回退归档；错误保留前后hash/读错/进度。

独占data/v4-study-031，干净提交，60秒/8MiB，最终写入后复查。metadata含status,planned_horizons33,completed_horizons,cohort_states52,max_horizon32,new_full_world_steps0,new_phase_transitions0,new_environment_sources0,reused_environment_sources20,selected_environment_sources11,new_independent_initial_worlds0,git_commit,elapsed_seconds,time_limit_seconds60,storage_limit_bytes8388608,input_paths,input_sha256,input_sha256_after,output_sha256；可保留input_inventory_errors/input_read_errors_before成功空dict。

proof核验503输入、33分布、52映射、四格摘要、metadata/records/summary三输出、自身hash和前后输入；独占写入和预算，异常保留。四根JSON完整逐字节归档。持续研究授权intentional fast-track；先RED闭式/吸收/概率守恒/边界/类型反例、两路线与审查、干净提交，再正式精确计算。第三独立作者审查不可用时如实inline fallback。

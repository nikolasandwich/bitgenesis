# 设计

合同为experiments/v4/study-018.md。三新脚本：scripts/copy_bottleneck_inputs.py、analyze_v4_copy_bottlenecks.py、verify_v4_copy_bottlenecks.py。旧物理、017工具、数据不改。

## 接口及精确模式

输入helper提供bindings/source_rows/read/digest。bindings在structure_copy_inputs的1617项上加入017五根JSON与其五归档、本协议、三新脚本，共1631项；核实017status/outputsha/独立凭据/归档字节。source_rows为旧40来源行，不含新科学分类。017 records另由两主程序按分支键索引传给算法。

生产接口analyze(initial,rows,final,copy_parents)，返回parents。核验独立recount同签名。copy_parents为017该分支父记录数组；对应身份、成员数、成员列表必须相等。四GATES按population,inventory,partition,copy排列；STATES按population_fail,inventory_fail,partition_fail,copy_fail,copy_pass。统计METRICS为四GATES各_ever/_persistent共8，summary额外五STATES时间比例共13。

records.json为40行history/seed/mutation/exchange/parents；每parent保留component/anchor_members/anchor_size，series四个长度400布尔数组、episodes四数组[start,end]、longest四整数、state_steps五整数。区间双端含，true为达标；计数为按population→inventory→partition→copy顺序的首个未满足门槛对应状态，每步唯一，合计400。测试短序列允许analyze/recount，但正式主程序与汇总要求400。

results.json为40行history/seed/mutation/exchange/status/eligible/counts(8整数)/fractions(8精确分数或null)/state_steps(5合计)/state_fractions(5精确分数或null)。状态分母400*eligible，即先每父400步比例后父等权；事件分母eligible。不得把状态计数当父事件分子。要求每父、每分支嵌套和总和成立。

summary沿017cells8/pairs20/groups4的顺序与字段，仅metrics为13项（8fractions加5state_fractions）。所有精确分数用str(Fraction)，零分母null；先来源内父等权，再5来源等权。生产branch_result/aggregate/summarize_records接口沿017；核验make_results/make_summary独立。

metadata沿017planned/completed40、输入前后、gitcommit、时间1200/存储200MiB、新模拟0/独立0/复用5、三输出哈希。data/v4-study-018独占；分支逐次落盘保留失败；核验独占independent-verification.json，检查40/824/1648/16000/2636800全部值，copy逐值吻合017、5状态和全汇总。

## 独立性

生产按组件计数及属性Counter，可缓存初始直方图；核验通过当步身份索引、每父筛选属性计数与完整组件逐一比较，不导入生产科学函数。017的copy序列是已独立核验的输入，两路线均复用；本项独立性只覆盖新增必要条件，不伪称第三次重算几何。

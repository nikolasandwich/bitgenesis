# 设计

合同为experiments/v4/study-017.md。新production规范化指纹与独立直接平移点集匹配，分别重建祖源与汇总，不共享科学算法。输入工具可复用horizon_fate_inputs.bindings的1613项，再加入017协议与本项三工具。

## 接口

scripts/structure_copy_inputs.py提供bindings()/source_rows()/read()/digest()；source_rows直接复用study016完整结果行，不含新科学分类。新增scripts/analyze_v4_structure_copies.py与scripts/verify_v4_structure_copies.py；输出data/v4-study-017。

四序列固定descendant_material/descendant_genetic/unrelated_material/unrelated_genetic，逐父组件每序列400个非负匹配组件数。records.json为40行history/seed/mutation/exchange/parents；parents按初始component序号保存component/anchor_members/anchor_size/impossible_double、series四数组、episodes四区间列表[start,end]（相对步、双端包含）、longest四整数。两个以上才为区间内真值；空序列区间=[]、最长0。

results.json为40行history/seed/mutation/exchange/status/eligible/counts/fractions；八指标为四序列各加_ever（最长>=1）和_persistent（最长>=10），其中descendant_genetic_persistent为主要量。分数为精确字符串，分母零null。主要量不另设会漂移的重复字段。

summary.json为cells8行(history/mutation/exchange/metrics)、pairs20行(history/seed/mutation/metrics[key]={on,off,difference})、groups4行(history/mutation/metrics)；cell/group metrics各key={mean,available,missing}。列表笛卡尔顺序history True/False，seed112000..112004，mutation0/100，exchange True/False。

metadata记录status、planned/completed_branches40、new_simulation_steps0、new_independent_sources0、reused_independent_sources5、git_commit、elapsed_seconds、time_limit_seconds1200、storage_limit_bytes200MiB、input_sha256/input_sha256_after、output_sha256映射records/results/summary。独立凭据independent-verification.json唯一写入；失败不得覆盖既有数据。

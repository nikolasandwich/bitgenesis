# Study046：首例双路线工程集成

本轮完成任务2.3的首例执行和证据归档，提交独立工程审查；任务状态由父控制层在审查及干净提交后更新。仅首E120005两arm，不运行其余27对，不产生全队列科学结论。对照需求4.1及设计的“文件结构计划”“组件与接口”“错误与验证”。

## 执行范围和结果

运行前HEAD为`8e549e6be3651df857f86349b92b94c0af4545d7`，工作区干净；无运行中的046脚本，无`data/v4-study-046`。不改代码、测试、旧数据、旧review/proof、冻结方法、tasks/spec或LOG。TDD不适用：本次为纯集成，不引入行为变更。

直接核验[既有最终生产归档](results/v4-study-046-engineering/producer/metadata.json)，没有重跑生产。实际调用为：

```sh
PYTHONPATH=src .venv/bin/python scripts/verify_v4_middle_refill.py --source-dir /Users/todd/Documents/bitgenesis/docs/research/results/v4-study-046-engineering/producer --output-dir /var/folders/b4/b68421jx7ls06zyxnzbsk95m0000gn/T/study046-task23-hg87jr8b/verifier --engineering
```

输出目录来自`tempfile.mkdtemp(prefix='study046-task23-')`，运行前verifier子目录不存在。仅调用一次，退出码0；完整标准输出为`complete 1 pairs; 208 slots; 0 physics`，标准错误为空。外部测时4.856583秒，核验证明记录4.660163秒，生产历史记录6.898857秒。两路线各600秒/134217728字节预算，新增核验五个JSON共1,512,957字节；既有最终生产五个JSON共1,510,117字节，均在预算内。新增/重放物理、环境来源及独立初始世界均为0。

|覆盖对象|实际范围|
|---|---|
|配对/arm|E120005一对，control/ablation两arm|
|未来保存态/诊断|26未来态；2个t0诊断独立保留|
|全源槽位/目标tick|208/52，每未来态8槽位、2目标|
|既有gap|7个，control 4、ablation 3；不重算045区间|
|完整索引|100项；28触发、72不适用、10短窗作为原索引信息保留|
|汇总|全部20格及零项；工程配对差只有1对|

[独立核验证明](results/v4-study-046-engineering/verifier/independent-verification.json)的执行及收尾均complete。`pair-01.json`、`records.json`、`summary.json`、`index.json`全部对象通过具体类型、键集合、列表顺序和标量值比较。集成另逐节点比对四文件，并记录双方规范化SHA256，见[全对象比较证据](results/v4-study-046-engineering/integration-run/object-comparison.json)。index原始字节一致；其他三个JSON因字典字段排列顺序不同，原始SHA256不同，规范化SHA256及完整类型/值一致。归档按各自产物原始字节保存，不改写为相同序列化。

## 来源与独立性

核验当前954个输入的开始/结束hash相同，生产五个文件和核验四个数据产物的开始/结束hash也相同。历史生产当时953输入仅缺尚未实现的核验器，其全部公共输入与当前954输入精确一致；生产metadata原样保留，不补写历史epoch。当前生产源码SHA256为`0c704f2322b94eff4474f09b985a99fee56cf69bdc987a225e815f69565dba47`，当前核验源码为`881c8dd4548700adb73811e2f45b37f1a05a9edc88619eeced21fb40bd92b8ac`。

生产与新增核验投影由不同实现上下文编写。核验器独立使用阶段与目标候选索引，不导入生产科学函数；两路线共享不可变来源工具与041既有提议值。041旧E/W提议不是本轮重新独立分类，原041“parent inline fallback”作者标识仍保留。空源/消解/未指向槽位和045缺口连接是046新增投影；不重跑042能量账、044组件或045区间。

生产初版和本版两个真实epoch及旧核验被拒版本均保留于[source-epochs](results/v4-study-046-engineering/source-epochs/preservation.json)和[被拒版本清单](results/v4-study-046-engineering/source-epochs/verifier-rejected-1-preservation.json)。首次REJECTED为任务2.2的合成中断/类型反例，不称为真实首例工程失败。本轮真实核验没有失败或重试；既有失败审查及旧源码未覆盖。

## 测试依据、正式入口与归档

运行前后均核对[任务2.2最终独立审查](results/v4-study-046-verifier-review.json)的978个绑定与当前文件一致，其SHA256为`4d8feb1dd6e4d873cd4d373ae202ab79162436b819a78e973a3ab6bb18fb62ca`。五个当前代码/测试文件均匹配该审查记录。该同版独立实测：966项全suite通过（64.819秒）、30项核验专项通过（6.668秒）、compileall/空白等检查通过。本次没有修改这些文件，因此未无原因重复全suite；本轮新增验证为实际CLI入口、首例完整对象比较和来源/归档核对。另实际执行compileall与diff空白检查，退出码均0；完整输出保留。

[正式入口检查](results/v4-study-046-engineering/integration-run/formal-entry-checks.json)仅静态核对并引用已有同版故障测试：正式默认要求核验器、干净提交和独占输出；工程仅首E120005；历史953子集只允许显式engineering。没有调用formal入口。结束时仍无`data/v4-study-046`。

[保存清单](results/v4-study-046-engineering-preservation.json)逐项记录新五产物及执行证据的原始路径、归档路径、bytes和SHA256。新verifier及integration-run归档目录均独占创建；完整stdout/stderr、实际参数、退出码、测时、运行前后绑定、对象比较和检查结果可复核。本报告仅申请首例工程审查，不宣称任务3、全队列分析或研究问题已经完成；独立工程APPROVED及干净提交是下一道门槛。

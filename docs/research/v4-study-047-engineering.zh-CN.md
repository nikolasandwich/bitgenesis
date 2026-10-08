# Study047：首E120005工程集成证据

2026-10-09。任务2.3的唯一首例工程已实际完成：生产与独立字典核验CLI各调用一次并成功，完整科学对象、当前来源和原始归档均核对通过。实施者状态为 **READY_FOR_REVIEW**；仍须新上下文独立工程审查、父层完成核验及干净提交，当前不能据此声明任务2.3最终完成或正式研究GO。

## 运行前固定与真实执行

具体问题和方法先固定在[运行前任务说明](results/v4-study-047-engineering/raw/task-brief.zh-CN.md)。从干净提交 `931dd9e70f6b89813635f7d25e74cdc8cf42e0bf` 执行，HEAD与origin/main一致，原工程根、正式根和工程归档均不存在，无其他Study047路线进程。生产审批1985项、核验审批3023项当前绑定逐一核实。两路线完成前仅写Git忽略的独占 `data/v4-study-047-engineering/`，执行包装器没有导入科学模块、额外抽票或重算。

两条真实命令按顺序执行：

```text
PYTHONPATH=src .venv/bin/python scripts/run_v4_middle_withdrawal.py --mode engineering --output data/v4-study-047-engineering/producer
PYTHONPATH=src .venv/bin/python scripts/verify_v4_middle_withdrawal.py --mode engineering --producer data/v4-study-047-engineering/producer --output data/v4-study-047-engineering/verifier
```

包装器为子进程显式提供完整环境，完整值保存在各路线request.json；PATH、HOME、TMPDIR、LANG仅在父环境存在时传递，并设PYTHONPATH=src，没有隐含继承其他环境变量。准确argv、工作目录、开始结束时间、退出码、源码前后hash、原始stdout/stderr均保存。冻结运行时为CPython3.14.2及POSIX后端，运行时/随机库字节由两路线输入清单绑定。

| 实际结果 | 生产 | 独立核验 |
| --- | ---: | ---: |
| CLI退出码 | 0 | 0 |
| metadata状态 | complete | verified |
| 包装器实测墙时，秒 | 11.046951458905824 | 12.251149791991338 |
| metadata内部耗时，秒 | 10.96941883303225 | 12.171375207952224 |
| 真实未来物理步 | 64 | 64 |
| 未来生成器tick | 32 | 32 |
| 过去生成器重建tick | 640 | 640 |
| 完成工程配对 | 1 | 1 |
| 输入前后及当前一致项数 | 1194 | 1200 |
| 路线预算 | 600秒 / 134217728字节 | 600秒 / 134217728字节 |

本轮共 **128真实物理步（64+64）**、**64未来生成器tick（32+32）**。各路线的640过去生成器tick分别为20seed×32，仅恢复过去抽签，不是物理重放。每路线未来只有120005一个seed的32tick，两arm共享自然后缀；没有其他27对未来抽签/物理，没有正式数据，没有真实失败运行或重跑。本轮没有新合成测试物理或合成未来tick。工程样本为1配对；独立核验不是第二个科学样本，工程也不抵扣正式28配对中的E120005。

## 完整对象、来源与未运行账

[只读自审结果](results/v4-study-047-engineering/raw/audit.json)核实两路线完整case、自然环境与tick64随机状态、records、100项index和summary的递归具体类型及全部值相同；这五份科学文件本次原始字节也逐一相同。metadata和核验proof属于各自路线证据，分别保存自己的原字节与hash，不声称它们相同。

原1192项冻结输入闭包不变。生产额外绑定两份执行审批成为1194项；独立核验再绑定全部6份生产文件成为1200项，均前后相同且自审时当前文件一致。已核对全部原Git跟踪文件在两次CLI前后保持不变，保存201份源码、测试及运行合同原字节快照。工程归档在两条路线完成后才创建。

两臂initial严格等于043 east/120005的 `/ablation/final`，原文件hash及终态规范化hash也核对。tick32共同身份/程序/材料/祖系完整保留，历史0/1仍在表中而不在alive站点中；原一次移除export=124仅作前缀旁账，047 export=0。逐步全256方向、仅101/102北向覆盖、固定四位置供能、全部突变票、能量与质量账通过保存数据核查，没有再执行物理。

100项索引保持：1项工程完成、27项 `not_run_engineering`、72项 `not_applicable_original_32_no_trigger`；后两类future均null。全选定队列E/W/S/N/H=5/3/0/9/11，工程完成数=1/0/0/0/0；五编码、零分母均值null、二元四格、14共享seed组和原10短窗标签均保留。14是原队列环境组数，当前真实后缀只运行1个环境，不能写成14环境已完成。

## 首例观察及解释边界

两臂tick32的完整新副本数q32=0。33–64的32个末态中，只有44–48的q为2，其余为0；完整序列、组件、成员、全程序、祖系、出生见证与失败零项均在case中保存。两臂的唯一双副本区间都是[44,48]，inclusive length=5，future_persistent10=false，左右删失均false，cross_boundary=null。所有记录的指标撤除减继续差为0，但形成提议失败账不同：继续/撤除的occupied分别65/59，raw_material分别86/92，collision均4，energy均37，formed均5；不能把指标相同写成所有输入和过程相同。

原t0=19。合格期保存的出生见证包括identity12在tick25、identity14在tick30，满足原t0后出生而不满足tick32后出生；两臂formation_supported=1，after32_formation_supported=0，after32形成见证为空。未来仍各有5次出生，不能把“无32后形成支持”误写成“未来没有出生”。

两臂共同账为E32=217、未来imported=549、rejected_import=475、spent=514、E64=252；spent由leakage203、bond286、construction20、copy5组成。初始活着6、未来出生5、自然死亡6、最终活着5；质量始终7，无重复移除或未来export。

这只是首例工程观察，不代表完整28配对撤除效果、无效应结论或生命标准达成。估计对象仍为既定北向处理前缀后的完整政策撤除；方向还影响程序材料表达，人工初态、外部供能和编码间共享seed的限制均保持。

## 容量和全队列投影

| 存储量，字节 | 生产 | 独立核验 |
| --- | ---: | ---: |
| 最终实际路线文件总计 | 2748098 | 2831087 |
| 完整case | 2001075 | 2001075 |
| 唯一环境文件 | 32129 | 32129 |
| records+index+summary | 220956 | 220956 |
| 最终管理文件 | 493938 | 576927 |
| 原metadata保存的全队列投影 | 64068546 | 63248394 |
| 用最终管理开销保守重估 | 64642426 | 64974382 |

最终管理文件在生产为metadata，在核验为metadata+proof。原metadata投影是源码在收尾前计算的原始值，归档未修改它。归档时另按完整最终管理开销计算：

```text
生产：2001075×28 + 32129×14 + 220956×28 + 493938×4 = 64642426
核验：2001075×28 + 32129×14 + 220956×28 + 576927×4 = 64974382
```

分别约61.648/61.964MiB，均低于134217728字节硬限。这是首例外推，不是其余27例大小保证；正式仍须逐写检查，不能删科学字段、缩队列或增加预算。墙时简单乘28为309.314640849/343.032194176秒，也仅为首例外推，不构成正式时限保证。原数据、源码快照和审计归档额外占用不混记为路线科学产物容量。

## 同版测试复用与检查失败保全

复用既有当前1070项完整回归PASS：内部77.334秒、wall77.773548秒、exit0，含104项Study047测试；五份当前源码/测试hash与前后绑定、当时源码快照和原始stdout/stderr逐项核对。当前同版编译与两CLI帮助证据已核实，实际两CLI补充真实工程smoke/集成验证。帮助证据中的CLI字节为当前版本，其所附测试快照早于后来仅合成测试时标调整，不声称其测试文件是当前版本；当前测试由最终1070项回归覆盖。

本轮没有科学模型或行为代码实现，没有新RED测试；沿用生产和核验独立批准中保存的真实RED、GREEN、边界/异常证据，不冒称本轮重跑。来源、严格类型、tick32/33、跨界9+1与未来10、出生双阈值、阶段异常、收尾失败、KeyboardInterrupt/SystemExit及预算控制的相关证据由原批准和当前完整回归覆盖。原生Windows未执行；缺POSIX接口模拟不是原生平台验证。

补充只读证据审计v1曾exit1：它将case.boundary.final的来源引用描述符误当终态对象。原脚本、trace、stdout/stderr和exit1保存在[post-check](results/v4-study-047-engineering/raw/post-check/execution.json)。v2仅纠正为核对path/pointer/原文件hash/终态对象hash，再严格比较两个arm.initial与043终态；[v2检查exit0](results/v4-study-047-engineering/raw/post-check-v2/execution.json)，wall1.1461487909546122秒。两版检查器都不导入科学模块，没有额外抽票/物理，不重跑两条实际CLI，没有修改任何研究源码或输出。

既有测试失败史继续保持原记录，包括先前联合full的2 errors、核验空metadata，以及当时生产临时失败目录已清理、只能保留trace/原始日志/源码的已知缺口。本轮不把该历史缺口改称完整保全，也不将合成失败账记入真实工程运行。

## 逐字节归档与待审门槛

[归档清单](results/v4-study-047-engineering/archive-manifest.json)包含全部236个原始文件的原路径→直接归档副本→tar成员映射、大小和SHA256，共8251010字节。涵盖两路线完整输出、请求/环境/退出码/时间/原始stdout/stderr、运行前问题/方案、runner、201份来源快照、只读自审和失败版本。全部236个成员实际从压缩归档恢复到新临时目录，与原文件和直接归档副本逐字节、大小、hash比较通过；临时恢复副本随后清理，原始data文件未移动、覆盖或删除。

压缩归档为[engineering-evidence.tar.gz](results/v4-study-047-engineering/engineering-evidence.tar.gz)，1101788字节，SHA256 `57c0ab9830a8a06725fcc6aa6c9a8290ab62cbde3515df63d927ab9094bf4f0e`。归档命令及原始输出在[archive-execution](results/v4-study-047-engineering/archive-execution/execution.json)。

独立审查入口为本报告、[封口清单](results/v4-study-047-engineering/validation-summary.json)、[生产metadata](results/v4-study-047-engineering/raw/producer/metadata.json)、[核验metadata](results/v4-study-047-engineering/raw/verifier/metadata.json)、[核验proof](results/v4-study-047-engineering/raw/verifier/proof.json)和完整归档。实施者未改spec/tasks/LOG、审批门槛、源码、测试，未commit/push。新上下文工程审查及父层干净提交完成后，才由任务3.1另启完整正式28配对两路线，各1792物理步；本轮保持正式目录不存在。

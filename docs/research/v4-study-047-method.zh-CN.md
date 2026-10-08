# Study047方法阶段：北向前缀后的方向控制撤除

本轮确认全部28个043北向处理分支的tick32完整终态可以无物理重放续接，并在任何未来抽签前冻结33–64的32步配对设计。方法阶段新增/重放物理均0，未来环境票生成0，未来科学结果0；`data/v4-study-047`未创建。当前是方法产物待独立审查，所有任务仍未勾，不宣称Study047研究完成。

最终有效入口为[scripts/audit_v4_middle_withdrawal_design.py](../../scripts/audit_v4_middle_withdrawal_design.py)，最终来源证明和清单为[design-revalidated-sources](results/v4-study-047-design-revalidated-sources.json)、[design-revalidated-census](results/v4-study-047-design-revalidated-census.json)。前一次成功方法epoch原件保留，不能将旧源码hash错误地对照当前已修复源码；对应关系见[epoch-1保存清单](results/v4-study-047-design-epochs/epoch-1/preservation.json)。

## 冻结问题和分母

[预注册](../../experiments/v4/study-047.md)与[规格设计](../../.kiro/specs/middle-policy-withdrawal/design.md)固定：每个既定043.ablation.final在32边界深拷贝，分别继续101/102北向掩码或撤除至共同自然方向票；差值为撤除减继续。自然票以同seed跨编码和两arm共享，空格也逐位置抽签。其余固定供能、突变票、物理和观察标准不变。方向同时影响材料表达，所以解释为完整方向政策撤除的条件效果，不能拆为纯机会效应、从未干预比较或自主生命出现。

| 编码 | 原索引 | 纳入配对 | 原32步N/A | 历史短窗 | 未来每路线计划物理步 |
| --- | ---: | ---: | ---: | ---: | ---: |
| east | 20 | 5 | 15 | 1 | 320 |
| west | 20 | 3 | 17 | 1 | 192 |
| south | 20 | 0 | 20 | 0 | 0 |
| north | 20 | 9 | 11 | 3 | 576 |
| homogeneous | 20 | 11 | 9 | 5 | 704 |
| 总计 | 100 | 28 | 72 | 10 | 1792 |

28分支只对应14个旧seed：120001、120003、120004、120005、120006、120007、120009、120010、120011、120013、120015、120017、120018、120019。编码间相关，不视作28独立环境。72原未触发保持未来null/N/A，不能称100案例64步结果。历史10短窗不使047新后缀变短；每个纳入arm都是32步。

## 状态和环境连续性证据

043完整保存units、raw、site_ids、parents、individuals；28终态均与最后保存物理状态相同。方法脚本独立消费原编码source到t0的保存事件，再消费043北向后缀，合计896保存tick，其中北向保存后缀390tick，逐行核对身份、出生/死亡字段、存活程序/材料，完整people与最终parent数组严格一致。它只读事件，不调用物理转移函数。每终态历史身份数11–18；世界材料质量7。

Observer恢复还需tick=32、founders=3、alive和完整individuals，下一ID等于历史长度。外部移除0/1保留在历史中且death_tick仍None；存活只由alive/site_ids判断，不能改写旧历史或计为新自然死亡。旧removals/export引用继承，047新export=0。原始匹配模板按各编码source.initial保持，不能替换为32终态或统一north模板。

真正环境生成器是019的copy-ablation命名空间，两条独立Random流分别由`v4-copy-ablation-1:{seed}:directions`和`:feeds`的SHA256整数初始化。每tick方向流顺序生成256次randrange(4)，feed流sample(range(256),4)。019/023/038/043没有保存可直接读取的RNG checkpoint，本轮是重建32后的状态，不能称已有checkpoint。

每次成功方法检查全20旧seed的640过去生成器tick/163840方向值；完整对照019 random-direction及random-both的32票、023/038对应编码原源和043掩码票，并核固定提议供能85/86/117/118各8、其余0、每位突变票[999,0,1]。random-both保存的是供能位置集合，不包含sample抽取顺序；本轮有序sample来自绑定实现重建，集合逐项可核。feed流在实际random-direction模式不用于供能，且与方向流独立。

清单保存全部20seed的完整32后getstate、其规范化hash和过去feed抽取顺序。运行时为CPython3.14.2、Random state version3，random.py、_random扩展、Python可执行文件及仓库生成器均绑定。E120005方向state SHA256为`0a4dfa0b965778f80d3499651ca62543189bfeca9bdcbbd4b6131593dafdb34a`，feed为`0a1f2adbb23be8eaab0c0fa2b2daa2f223c3d4df0c419c77a2eda3422114d862`。后续实现必须独立匹配旧32票及状态后才继续33；不能按占据跳抽、按arm推进同一可变RNG或用新seed替代。

## 方法两epoch和修复

两次均是在基准HEAD `ded56e9f93249640382d9d8db246003daf9d1ae2`上的未提交方法新增文件执行；方法运行本身不要求干净新提交，未来真实工程/正式运行要求干净提交。两次不是不同独立科学路线，而是同作者方法实现的成功首轮及必要修复后的来源/结构复验。

| 方法epoch | exit | 内部秒 | wall秒 | 输入绑定 | sources字节 | census字节 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 首次成功 | 0 | 3.904737 | 3.951046 | 1167 | 359885 | 786521 |
| 修复后复验 | 0 | 3.864929 | 3.926877 | 1178 | 934091 | 786521 |

两份census原始字节完全相同，SHA256均为`0c4e013cd7766f8e502c4efd948eba3b5fbb9920947ab5998eedf5ca0fadeaf8`；来源证明增加了旧epoch、故障测试和分阶段真实hash捕获。每次都各重建640过去RNG tick，方法两次共1280过去生成器tick；这些不计物理或新样本。所有方法产物远低于600秒/128MiB。

首次成功后，父层代码审查指出三个异常证据问题：hash读取捕获BaseException后可能改抛ValueError、首次来源预验证失败时未保存已读hash、第二独占文件创建失败可能留下running。原首轮没有遭遇这些异常，不标为实际研究失败。修复后逐阶段保存真实捕获的hash/读错，保留第一个异常对象并传播；两个文件分别取得所有权，收尾只写本次拥有的文件；各项收尾独立尝试，晚期异常也使状态失败。

原源码按首轮清单SHA256 `81d3340b2ad8ed71bebb1cf3e59b810a90a9f7d1ad50e94fcf8b1d91ed0c0819`逐字节存档。最终1178输入前后hash一致；旧1167绑定中原源码路径通过epoch-1归档验证，其余原路径仍精确相同。科学协议、需求、设计、research和首轮证据没有因复验改写。

5项合成I/O测试覆盖7个故障分支，最终同版实际PASS0.076秒：捕获KeyboardInterrupt/SystemExit保持原对象，坏hash证据留存，第二输出创建竞争保护外来文件，收尾两类中断仍保存failed，首异常优先。测试在临时目录、来源阶段或单独收尾函数执行，没有进入过去RNG科学循环，更没有未来票/物理；真实测试源码、stdout/stderr和exit保存在[复验运行目录](results/v4-study-047-design-revalidation-run/)。不冒称TDD先失败记录，不把合成故障称真实研究失败。

初次命令、stdout/stderr、exit/计时保留在[首轮运行目录](results/v4-study-047-design-run/)，修复后真实命令和源码hash保存在[method-execution](results/v4-study-047-design-revalidation-run/method-execution.json)。没有覆盖或清除旧成功epoch。

## 未来观察与预算

窗口在未来未知时固定33–64，因为它是与原32步相同的有界后缀并可容纳持续10标准，未根据未来数据选窗。tick32只诊断，主终点仍是实际至少2个完整遗传新副本在33–64连续至少10末态；完整组件、完整四项程序、材料、原0/1祖系及非创始成员条件均不放宽。

跨界区间仅在q32与q33都>=2时连接既有尾区间，分别记录过去长度、未来长度、合并观察长度及64右删失；合并持续10不能代替future持续10。出生时间保留原t0后和32后两种见证，不能把首次合格当出生。旧summarize_arm默认使用arm.initial.tick，因此047须显式双阈值适配，不能直接复用造成定义漂移。保存全部能量/材料/事件/身份账和阴性、S零格/零分母null。

未来首工程固定E120005两arm共64生产+64独立物理步。工程审查/干净提交后正式完整28对，重新包含E120005，1792+1792步；工程和正式不同epoch，总计划3712新物理步，0前缀物理重放，样本仍28配对/14环境。每路线600秒/128MiB；完整轨迹compact JSON、索引与汇总不重复嵌轨迹，工程实测预算。超限保留失败，不删科学字段、缩队列或默增预算。以上未来全部尚未执行。

## 验证状态与接续

fresh子上下文`/root/withdrawal_method/task_graph_review`初审三处局部问题后唯一复审PASS：13需求全覆盖，阶段1.1→2.1→2.2→2.3→3.1、边界和未勾状态合理。[任务图记录](results/v4-study-047-task-graph-review.json)保留真实初审/复审及生成时tasks文本。该快照中的“用户指定阶段号”措辞来自父工作分解说明，当前tasks已改为“本研究采用阶段号”；这不是另一个人类指定编号的证据，快照不改写。任务图审查不代替完整独立方法/来源审查。

本轮新审计脚本py_compile、真实两次清单、5项故障测试及新增文件空白/JSON/差异检查为方法范围证据；未执行无关966项物理fixture suite。完整独立方法审查尚待父层派发；因此只请求READY_FOR_REVIEW，不勾1.1、不更新父LOG、不提交。后续第一步仍是方法审查通过后的生产实现2.1，绝非直接正式运行。

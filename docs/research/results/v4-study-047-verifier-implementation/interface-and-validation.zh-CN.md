# 任务2.2：独立核验器接口与作者验证

本轮仅交付核验实现和合成测试，状态为待独立审查。未运行真实047工程/正式入口，未产生120000–120019任一真实环境的未来票或新物理，未创建data/v4-study-047。方法及生产批准来源保持原字节，不修改任务状态、规格、旧代码或旧报告。

## 独立路线

核验器只共享middle_withdrawal_inputs的不可变读取、绑定与严格具体类型合同。底层物理直接使用exchange_branch_audit.physical_step，结构分区使用structure_audit.reconstruct；不导入生产恢复、未来票、观察、区间或汇总函数。

- restore_environment：独立SHA256命名空间、两条Random流消费过去32票，逐项核对019两模式、固定供能/突变、完整checkpoint及冻结运行时；继续刚刚消费过的原流，没有以setstate替代历史证明。
- draw_future：每seed一次生成33–64票；每票256方向和4个feed有序抽样，返回只读映射与嵌套tuple。中断保存未完成方向、完整已成票、两流状态与状态读取错误。
- reconstruct_prefix：只消费既有保存的出生/死亡事件，独立推进被动历史、组件和完整程序匹配；不重演过去物理。最终历史须逐值等于tick32全表。
- reconstruct_arm/reconstruct_pair：保持原ID与历史移除旁账，独立字典物理、身份、组件/全程序/祖系、提议全部门槛、原t0及32双出生阈值、未来和跨界区间、完整账及配对差。模板使用原encoding初态；允许同一原创始祖系的两个匹配成员。
- record_for/build_index/summarize：完整100索引、72 N/A、工程27未运行、E/W/S/N/H的5/3/0/9/11选中数、14共享seed、全部二元四格和28个撤除减继续差。合成指标表有独立数值期望，并与生产接口作整对象对照。

CLI为`--mode engineering|formal --producer 既有只读epoch --output 全新独占epoch`。先检查同版干净git与独立2.1/2.2审批；formal还要求2.3工程审批。生产元数据的输入闭包包含bindings(True)及各阶段审批路径并集，工程为1192来源加两审批、正式再加工程审批。生产完整输出清单、原字节hash、具体类型、模式、64/1792步、完成数和冻结运行时均验证。独立重建之后对每个完整case、environment、records、index和summary作严格对象比较；两路线JSON字节可以不同，保留各自原字节hash。

## 失败与时间边界

真实入口使用从run开始的同一绝对600秒上限，工作最多570秒，余量用于收尾；固定32未来步不缩窗。每次写入检查完整写入长度和存储；收尾输出hash还与首次实际序列化字节的hash对照，拒绝写后漂移。

父进程执行全部独立收尾动作，逐项分配原剩余时间，保存首BaseException与后续错误。父计时器释放前磁盘状态保持closing或failed。最后只把证据提交交给短寿命POSIX子进程，使用原剩余预算的有界份额；子进程不执行科学计算，每条路径均在finally中os._exit。父进程中断或超时先终止并有界确认子进程退出，禁止迟到成功writer与失败writer并发。子异常经私有pipe保留类型、消息及traceback；父原异常优先。

metadata是完成提交，proof单独描述重建证据；须以整个epoch和实际CLI退出结果验收，不把单个proof或某个旧失败测试目录中的verified字样视为阶段批准。永久存储故障、持续不可用的计时接口或OS不可中断调用可能阻止最终证据保存，绝不授权成功；状态会停留在非完成或失败，且异常继续传播。真实入口要求POSIX计时器和fork；能力模拟不是原生Windows验证。

## TDD与失败epoch保全

首次测试在新入口不存在时实际ImportError，red-01的exit1及测试源码已保留；此RED形式获父层允许，未声称使用过临时feature flag。后续真实RED记录分别覆盖父计时器/child中断和错误运输、票对象可变、finally成功返回吞关闭错误与起始时间、短写/写后漂移以及child setup穿出边界。每次执行都有独占目录、原stdout.bin/stderr.bin、退出码、wall与当时源码副本及SHA256。

red-05中的旧实现曾错误产生verified合成目录；它们作为反例原字节留在失败测试epoch内，不是已批准研究产物。修正后相同反例拒绝通过。green-03-boundaries起，执行器把测试临时runtime epoch复制到该次执行的runtime-epochs，保存实际失败元数据、部分写入、错误和hash，不重写以前证据。

## 当前源码的实际验证

| 验证 | 结果 |
| --- | --- |
| 专项 | 45项，exit0 |
| 生产+核验相关 | 92项，exit0 |
| 缺POSIX接口模拟 | 45项，exit0，12项能力skip；非原生Windows结论 |
| compileall src scripts tests | exit0 |
| 核验CLI --help | exit0；未运行真实compute入口 |
| canonical完整unittest | 1058项，64.690秒，wall65.046327秒，exit0 |

最终专项每次真实执行65个独立字典kernel步、64个生产对照kernel步；核验生成器65个合成未来tick，独立测试参考生成器另32个，总计97。仅seed987654，mock不计入kernel或未来tick。相关与完整套件另外包含旧2.1测试的66合成物理及99合成未来tick。完整回归还有其他既有研究测试，不能把上述047计数冒充全仓库物理总量。

green-01和red-02的原stdout当时只列核验未来33，未分列参考循环32；源码快照证明参考循环实际执行，最终manifest按每次执行补充此32，不修改原日志。所有执行的047合成计数详见final-validation.json；这些均不是研究重复。真实047未来/物理始终0。

最终来源1192项前后一致，原producer审查1321项仍全部有效。当前源码和测试hash、每次原始执行证据hash、全证据目录逐文件hash与保全说明在final-validation.json。作者只请求fresh独立审查，不自授APPROVED，不声明TASK完成或FEATURE_GO。

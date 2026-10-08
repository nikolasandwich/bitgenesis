# R1修复Task Brief

任务仍为middle-policy-withdrawal 2.2，Boundary Verifier；原需求和设计范围不变。首轮独立REJECTED为verifier-review-initial.json（R1，需求4.2/4.3及失败、预算与测试策略）。

根因：run预检构造的Guard从未安装，进程检查和审批读取处在Epoch.execute之外。同一started只防止重获预算，不能中断sleep/I/O；预检耗尽时间后所有失败写入也失去预算。0.2秒配置的0.5秒审批延迟实际0.509153秒且空目录，符合此机制。

验收：进程检查、clean-git与审批读取都在从run起点计算的同一计时保护及首异常保全边界内；审批未过不读科学future或调用物理；超时留下failed而不是空目录；审批真实读取异常原样传播并留下证据。空输出目录不得使clean git误判为dirty，任何预先存在的dirty必须继续拒绝。工作与收尾继续共享原绝对deadline，不重启预算。

最小方案：Epoch.execute支持可选preflight，安装Guard后的工作租期先执行预检，首次metadata写入在审批成功后；run先独占空目录，Git不跟踪空目录。失败由既有统一收尾生成证据。科学重建不改变。

先追加控制面反例并实际RED；targeted GREEN不运行物理。父层确认上游Producer稳定后再做专项、相关、portable、compile/help及一次同版全套；最终新增final-validation-remediated.json。旧final-validation、所有历史源码、原始日志、审查/归档均不覆盖。真实047未来与物理保持0。

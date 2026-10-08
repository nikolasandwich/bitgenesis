# Study047续接与撤除接口

权威科学合同见[预注册](../../experiments/v4/study-047.md)，组件/文件边界与需求映射见[规格设计](../../.kiro/specs/middle-policy-withdrawal/design.md)。本文件固定实现者最易误解的入口。

- 入口只取043.ablation.final的tick32完整状态。两臂名`continue_north`与`withdraw_to_natural`，差值始终撤除减继续；旧043.control仅旧研究，不能当047初态或答案。
- 原0/1移除后的历史仍在individuals，death_tick可以None；恢复alive而不是从death_tick推算存活。Observer tick32、founders3、完整individuals和下一ID必须连续，不从末态新建创始编号。
- 真正环境源是019 copy-ablation命名空间两个独立Random流；023/038仅复用旧32票。方法只恢复过去32抽签并保存getstate，未来实现从32后继续。固定供能及突变票不是hereditary_runner的drive/mutation随机流。
- 101/102继续固定3，撤除保持自然方向原值，空格也处理；两个arm和同seed不同encoding读同一自然票，不共享会被按分支推进的可变RNG对象。
- original_template始终指该encoding原source.initial。完整组件/材料/程序/祖系匹配不变；q>=2与持续10保持，t32诊断不入future。旧t0后出生与32后出生单列；cross_boundary只描述已观察相连区间，不替代future_persistent10。
- 方法清单只存过去环境和来源/状态结构，不计算33+票或任何新物理。方法结果不可覆盖，任务图与独立方法审查通过后父层才可标1.1完成；2.1/2.2/2.3/3.1在后续执行。

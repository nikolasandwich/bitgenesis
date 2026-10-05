# 设计

## 1 数据责任
新增reformation_barrier_inputs.py只负责IO及036旧绑定；analyze_v4_reformation_barriers.py使用snapshot和直接slot条件；verify_v4_reformation_barriers.py独立重建材料组件与身份父链，不导入生产科学计算。tests各自同名新增。旧模型/数据不改。

## 2 交换格式
records为20个case，每个含selection、diagnostic、rows、transitions、episodes、longest；row含tick、三个slots、upper_failure、connector_sites、new_copy_count、出生死亡；具体字段由两作者实现前对齐。summary按两程序和两窗口层（short_window/remaining_conditional）完整四格及overall保留八谓词/七失败类别/事件数/三个持续指标。

## 3 验证与交付
TDD边界测试，首案例工程smoke，父全suite+compile后干净提交正式运行。两路线来源SHA256前后相同并逐字段对比，根JSON完整归档。协议037是完整科学契约。

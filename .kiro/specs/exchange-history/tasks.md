# 任务

- [x] 1.1 固定完整双向历史协议与边界。
  - _Boundary:_ 需求1及冻结协议，当前研究授权。
- [x] 2.1 实现对称历史分支与独立审计。
  - _Depends:_ 1.1
  - _Boundary:_ 需求2，scripts/history_exchange_branch.py、history_exchange_audit.py及专项测试。
- [x] 3.1 实现固定队列、历史交集汇总与独立核验。
  - _Depends:_ 2.1
  - _Boundary:_ 需求3/4，study015编排/验证及测试。
- [x] 4.1 完整执行、核验并发布全部结果。
  - _Depends:_ 3.1
  - _Boundary:_ 需求1–4，报告/归档/索引。

- [x] 5.1 固定全部两历史人口路径事后方案。
  - _Depends:_ 4.1
  - _Boundary:_ 需求5；无新增模拟。
- [x] 6.1 实现事件/身份双路线人口路径与完整绑定。
  - _Depends:_ 5.1
  - _Boundary:_ 新三脚本及专项测试，不改旧工具。
- [ ] 7.1 执行全部160分支核查、归档完整路径和结论。
  - _Depends:_ 6.1
  - _Boundary:_ 完整旧轨迹与报告，不挑结果。

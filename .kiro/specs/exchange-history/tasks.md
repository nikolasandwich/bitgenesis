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

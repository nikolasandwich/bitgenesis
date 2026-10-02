# 任务

- [x] 1.1 固定并inline审查新来源协议。
  - _Boundary:_ study014与本规格，用户连续研究授权。
- [x] 2.1 实现新队列编排、独立保存记录验证及反例测试。
  - _Depends:_ 1.1
  - _Boundary:_ scripts/run_v4_study014.py、verify_v4_study014_summary.py及tests，不改模拟。
- [x] 3.1 干净提交执行全部基线/分支，完整核验及报告归档。
  - _Depends:_ 2.1
  - _Boundary:_ 新队列完整结果；失败不缩队列。

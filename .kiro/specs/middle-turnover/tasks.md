# 任务

- [x] 1.1 冻结方法、验证完整来源/身份清单及042复用映射，完成方法审查。
  - 完成时两个只读清单可追溯全来源/56arm与35复用身份，来源前后hash一致且独立方法审查APPROVED；科学分析尚未运行。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1_
  - _Boundary:_ 仅experiments/v4/study-045.md、docs/design/v4-middle-turnover.zh-CN.md、scripts/audit_v4_middle_turnover_design.py及两个design来源/清单JSON、本规格文件，以及父上下文负责的docs/research/v4-study-045-method.zh-CN.md、docs/research/results/v4-study-045-design-review.json；不运行科学周转分析/物理，不创建data/v4-study-045。已由turnover_method_review新上下文审查APPROVED；仅方法阶段完成。
- [ ] 2.1 集成两独立只读路线、首例工程、测试/干净提交和正式全队列审计及归档报告。
  - 完成时两路线的全部身份事件、间隙/门槛时序和全20格汇总相同，前后来源hash通过，正式产物逐字节归档且0物理；先26态工程再测试及干净提交最后正式队列。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1_
  - _Boundary:_ 仅新增045输入绑定/生产/核验/测试/数据/结果报告；复用042旧8arm账、补48arm所需事件。不改旧来源、物理内核/政策、窗口或生命标准；每路线600秒/128MiB，0物理。1.1审核完成前不执行。

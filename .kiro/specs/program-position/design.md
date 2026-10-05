# 设计

## 1 输入边界
program_position_inputs.py仅IO与旧037/036来源链校验。run_v4_program_position.py使用现有内核生成E/W/S，不改变原模型文件。每case含encoding、seed、config、initial/rows/final、copy观察及指标，模板必须取各case.initial。

## 2 核验边界
verify_v4_program_position.py独立字典物理、身份/组件及模板匹配，不导入生产科学函数；旧019/023参照只读核观察。生产及核验都不做原组移除。完整字段由实现前对齐。

## 3 完成边界
任务1.1为方法审查和来源可行性，仅文件读取无模拟；2.1为代码、测试、正式运行及报告。依据协议600秒/128MiB限制，两路线工程仅首east seed。规格phase保持tasks-generated直到2.1完成。

## 4 方法审查澄清
H−H为完整参照表的恒零行，不算额外证据。工程首east试运行和重算单独记账，正式1920仅指正式60案例，不是累计物理调用量。方法决策及来源清单见docs/design/v4-program-position.zh-CN.md。

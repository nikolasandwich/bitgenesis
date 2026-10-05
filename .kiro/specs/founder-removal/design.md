# 设计

## 1 边界
协议036是完整科学契约。新增scripts/founder_removal_inputs.py只负责来源清单及哈希；run_v4_founder_removal.py用既有内核/Observer/结构观察实现；verify_v4_founder_removal.py不得导入生产实现，用既有exchange_branch_audit字典物理及独立身份/组件分析实现。各自tests/test_v4_founder_removal*.py。不得修改旧内核/报告/数据。

## 2 交换格式
生产者先发布分支/记录格式供核验者对齐；结果保存data/v4-study-036/{metadata,records,summary,independent-verification}.json及cases/branch-NNN.json，每case含selection、control、ablation，各臂initial/rows/final/metrics及见证。独立者可复用纯IO/hash清单，但不得复用科学计算；全部分支重新算并逐字段比对。摘要12来源格、三层和四格配对结果保留零项。

## 3 验证与运行
先有意义的边界测试RED→GREEN；只用首入选案例做工程冒烟，不全队列预跑。父审查代码、全suite与compile，再干净提交正式运行；执行预算与失败记录、来源绑定及恢复核验按协议。不改已有初态、票、观察窗或生命标准。

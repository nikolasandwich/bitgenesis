# 设计

遵循experiments/v4/study-024.md第1–4节。新scripts/program_boundary_inputs.py只负责IO/绑定；analyze_v4_program_boundaries.py和verify_v4_program_boundaries.py分别复用020/021的生产与独立算法，新增形成账本分别取提案和身份差。记录genotype/seed/exchange/phases/members/formations；formations为32个列表，各事件child/parent/site/material，按child排序。四格摘要固定顺序均一关/开、异质关/开。

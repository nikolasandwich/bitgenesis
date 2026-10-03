# 设计

完整合同：experiments/v4/study-020.md。

API：analyze_case(case)输出seed/mode/exchange/steps/episodes。steps每行tick/previous/dissolved/final（各为排序的匹配身份组列表）、births/deaths（排序身份）、crossings（按dissolution_up,dissolution_down,formation_up,formation_down固定顺序bool列表）、hidden（bool）。episodes行start/end/length/right_censored/start_step/exit_step，后二者为对应steps整行或null。summary为六行列表：mode/exchange/cases/episodes/double_steps/dissolution_up/dissolution_down/formation_up/formation_down/hidden。三模式顺序random-direction,random-feed,random-both，exchange False/True。核验独立recount(case)及aggregate(records)遵守相同输出接口；共享helper只溯源。

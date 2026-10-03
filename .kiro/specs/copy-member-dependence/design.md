# 设计

合同experiments/v4/study-021.md。

analyze_case(case,label)返回label/steps/episodes/new_episodes/new_longest/new_persistent10。标签label为019文件stem（seed-120000-random-direction-exchange-false等）或control-constructed-off/control-constructed-on/control-no-raw-off。steps行tick/copies（按members排序的组字典）/new_only_count/founder_containing_count；每组members/original_members/depths/founder_roots/all_new。episodes行start/end/length/right_censored/stable_groups/stable_pair/max_same_pair_run；new_episodes仅[start,end]数组，new_longest为int，new_persistent10为bool。

summarize(records)返回cells六行及controls三行。每行键label（六格为random-direction-exchange-false等；对照为control-...）、cases/episodes/double_steps/all_new_double_steps/ever_two_new/persistent_two_new/stable_pair_episodes/max_same_pair_run。顺序三mode各false/true，然后constructed-off/constructed-on/no-raw-off。核验独立recount(case,label)、aggregate(records)同schema。helper source_cases() yield (label,case) 按019 GRID，然后三个对照；只提供读取，不含新科学量。固定label用于控制类别不能从阳性结果选择。

metadata同020加planned_cases123/completed_cases/saved_steps/new_simulation_steps0/new_environment_sources0/reused_environment_sources20/reused_deterministic_controls3/new_independent_initial_worlds0/git_commit/budgets/inputbeforeafter/outputhash。输出records.json123行、summary.json上述字典，proof全量独立字段比较。

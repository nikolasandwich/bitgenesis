# 设计

合同为docs/design/v4-horizon-fates.zh-CN.md。生产与独立核验脚本分离，只共享输入清单；两路分别重算分类和汇总。原模拟与旧工具不改。输出metadata/records/results/summary及independent-verification，保存全部分支与来源。使用每步活身份限制最终父链中的未来后代。

## 工具接口

共享脚本horizon_fate_inputs只提供`bindings()`（相对路径→SHA256）、`source_rows()`（study016 results各行加`records`四检查点记录）、`read(path)`、`digest(path)`。生产analyze_v4_horizon_fates、独立verify_v4_horizon_fates不互相导入。源目录data/v4-study-016，输出data/v4-study-016-fates。

records.json为40条分支身份行，每行含history/seed/mutation/exchange及components数组；仅初始合格组件。每组件保留component/anchor_members、checkpoints（每相对时点category/original_survivors/descendants/continuous）、first_break_tick、first_complete_replacement_tick、first_break_state、order。

results.json各行保留history/seed/mutation/exchange、status完整、eligible，checkpoints各时点有counts/fractions五类；timing有counts/fractions（两事件区间、顺序、首断开状态扁平键）。分数用精确字符串，零分母null。

类别键固定extinct/continuous_retained/continuous_replaced/broken_retained/broken_replaced；区间键001-100/101-200/201-300/301-400/never；顺序键neither/break_only/replacement_only/break_first/same_tick/replacement_first；首断开状态extinct/fragmented/mixed/closed_singleton/never。timing扁平键形如break_bin:001-100、replacement_bin:never、order:same_tick、break_state:mixed。

summary.json包含checkpoint_cells（32行history/mutation/exchange/tick/metrics）、checkpoint_pairs（20行history/seed/mutation/checkpoints[tick][类别]={on,off,difference}）、checkpoint_groups（16行history/mutation/tick/metrics），以及timing_cells（8行history/mutation/exchange/metrics）、timing_pairs（20行history/seed/mutation/metrics[扁平键]={on,off,difference}）、timing_groups（4行history/mutation/metrics）。cell/group的metrics[类别或扁平键]为{mean,available,missing}。列表顺序均history True/False、seed升序、mutation0/100、exchange True/False、tick100..400的适用笛卡尔积。

## 事后个案补充

需求5依据docs/design/v4-transient-case.zh-CN.md，新增独立两路线，不修改先前已完成工具或绑定。case输入与输出接口在实施前明确；用户持续授权作为有意快速推进批准。

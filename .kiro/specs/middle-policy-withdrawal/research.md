# 研究与设计决策

## 摘要

这是已验证离散世界的续接扩展，进行本地集成型发现，不引入外部服务或新算法库。查读AGENTS、Study046最新LOG/结果/formal-review/validation、043生产与来源、019/023/038实际生成路径、Observer和完整副本匹配。使用kiro-spec-quick、requirements/design/tasks及其EARS、review gate、discovery-light、synthesis、任务图规则；完成声明由kiro-verify-completion限定。用户持续研究授权按intentional fast-track生成需求/设计/任务，但内部独立审查不可省略。默认三份core steering不存在，如实记录。

## 发现记录

1. `run_v4_middle_north_policy.run_arm`保存final的units/raw/site_ids/parents/individuals，且32步末态在043旧窗口内。Observer还持有tick和founders；它们由32和原始3确定，完整被动事件账可验证。移除操作只改alive/units/raw，原0/1 history.death_tick不改，必须继承旁账。
2. `program_position_inputs.source_path`中north指023，其他原环境指019；E/W实际编码source为038，其方向票仍由019继承。019 `run_v4_copy_ablation.tapes`种子前缀不同于hereditary_runner。每seed两独立流，方向randrange与sample有固定tick顺序，不能直接跳过底层word数。
3. random-direction固定四位置供能与零突变票；feed流旧抽签在该模式未用，但可通过random-both保存32输入集合验证。RNG原checkpoint不存在；新方法生成的state必须明确是过去抽签恢复，并绑定当前Python实现和旧票逐项相等。
4. 完整遗传新副本沿`match_copies`且整个组件，世界级q>=2区间允许更换成员，不能误升级为同一双副本持续。新生after32见证与原t0后见证必须分开。

## 方案比较与决定

采用原32边界完整fork和过去RNG重取，避免重新物理运行前缀。采用全部28分支共同32后缀，窗口在未来未知时固定；不按三个既有末端阳性筛选。工程和正式使用分离epoch，正式仍重跑全部28，真实总预算3712，科学样本不增加。

没有引入通用checkpoint框架或修改旧内核：047仅需显式恢复有限Observer/物理状态和固定两流，薄适配更容易审计。生产/独立核验仅共享不可变来源合同；科学计算必须分别实现。源/状态不符时拒绝执行，不能用近似环境续接。

## 风险与后续核验

运行时抽签实现、来源字节或事件历史不一致均为阻断；方法脚本完整逐票/历史核验才可作可续接性结论。材料表达仍受方向控制；撤除效果不等于自主性。14seed跨编码共享，全部28不是独立环境样本。未来运行/区间统计尚未执行。本轮独立任务图审查与方法审查各自记录真实模式和结果，不冒称当前作者完成独立科学审查。

## 任务图审查记录

fresh上下文`/root/withdrawal_method/task_graph_review`轻量初审NEEDS_FIXES，指出2.1首例权限冲突、需求3.4措辞歧义及1.1遗漏明确046/043来源门槛；已局部修复，唯一复审PASS。13需求全覆盖，阶段1.1→2.1→2.2→2.3→3.1边界/依赖/完成条件合理；全部未勾。review只覆盖任务图与规格自洽，不替代后续独立来源/方法审查。

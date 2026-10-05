# Study026：北向形成机会与执行分支

## 1 固定范围

只读019全部120均一轨迹，以及02340+02580异质轨迹：两程序×三输入模式×20来源×交换两臂，240案例、7680保存步。0新模拟、0新环境/初始世界；全部方向、零案例和哨兵祖源保留，独立重放只是核验不是新增实验。

## 2 逐单元账本

每步列出步前全部存活单元（不把空位置随机票当机会，不纳入当步新生）。字段：tick/site/identity/root/direction/proposed/accepted/energy_before/energy_interaction/target/target_occupied/raw_available/reason/encoded_material/formed_material。root为最初0/1/2；目标谱系为root0或1，哨兵单列于all与target差。

消解后形成前的目标占据与原料用于target_occupied/raw_available；energy_interaction是输入、泄漏、连接和交换后、消解前能量。能量0的reason=dissolved，不曾进入提案；其他reason取energy/occupied/raw_material/collision/formed。encoded_material只是程序对应方向编码，不代表成功表达；formed_material只在formed存在，否则null。

生产从已保存interaction_units、proposals与前态身份读取；核验独立字典physical_step重建完整每步物理、遍历祖链，不调用生产分析。accepted生产取保存inputs，核验从前能量/容量/提议重算。核查完整形成/消解身份差、能量总账及出生不在当步行动者中。

## 3 摘要与解释

12格固定genotype homogeneous/heterogeneous→mode random-direction/random-feed/random-both→exchange False/True，每格20。每格all与target各统计actor_steps/proposed/accepted/north_tickets/north_proposals/north_nonzero_formed、reasons六键和north_reasons六键。北向票包括后续消解者，北向提案排除消解者。

另north_predicates键0..7为存活北向行动者的联合条件掩码：能量<16为1，目标被占为2，原料<1为4；0表示三项都满足，仍可能碰撞。联合条件可共存，记录reason按既有优先顺序执行，不能当独立必要因果。proposed/accepted为对应步前单元位置之和，不能混同每案例全256位置提议1024。所有原始输入与阴性已保全，本轮不新增干预。

## 4 工程与保全

helper north_opportunity_inputs.py只做IO/绑定，analyze_v4_north_opportunities.py生产、verify_v4_north_opportunities.py核验。analyze_case(case,genotype)/recount(case,genotype)返回genotype/mode/seed/exchange/steps（32个列表，单元按site升序）。summarize/aggregate接受固定240有序完整记录，返回12格列表字段genotype/mode/exchange/cases/all/target。

继承025的295绑定，加80新case、025四根源/四归档8、tar+恢复清单2、本协议及新3脚本4，共389。source_cases顺序genotype→mode→exchange→seed返回(genotype,Path)。来源初始校验失败也保留可恢复清单及逐文件hash/读取错误。

独占data/v4-study-026，干净提交，300秒/64MiB；metadata/records/summary及独立proof完整逐字节归档。metadata完整240/7680、0新模拟/来源、20复用环境、输入前后/代码绑定、输出hash、预算/耗时；失败记录不覆盖。核验完整物理与新账本/摘要，核验器自己hash绑定。先反例后实现、全套回归、独立审查、报告状态提交推送。

## 5 授权

用户持续自主研究授权下intentional fast-track。旧物理、10步生命相关观察标准不变；本轮只解释过程分类，不能升级自主繁殖或普遍不可能结论。

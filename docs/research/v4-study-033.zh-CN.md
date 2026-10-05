# Study033：逐位置材料守恒与北向目标限制

## 结论

全240保存案例、7920快照、2,027,520位置检查中，`raw(site)+占据(site)`相对初态的偏差为 **0**。所有案例的初始材料支持集相同：`[85,86,101,102,117,118,204]`，每格恰好1，其余249格为0。完整独立物理重放与库存审计一致。

现规则不迁移材料：输入、泄漏与交换只改能量；死亡在原位返还原料，形成在目标原料与目标占据之间转换。因此从这些初态出发，新单元不能在这7格之外形成。这是规则不变量与保存轨迹共同支持的限制，不只是32步观察中碰巧未发生。它不否认支持集内部的再生、程序表达或结构复制，也不等于生命不可能。

双随机每种程序、合并交换两臂的513次目标北向存活提案：**333次初始无材料、154次被占据、26次空闲且有原料**；最后26次能量全不足，没有三条件齐备候选。两个程序计数相同。无原料并非都表示“已有原料被耗尽”；本轮把空间上原本就没有材料和仍在位置上但已成单元的材料区分开。

## 预先范围与机制推导

[协议033](../../experiments/v4/study-033.md)冻结提交`f106bd6`。来源为026已核验的全部240案例：019均一120、023异质方向40、025异质供能/双随机80，20既有环境种子跨模式/程序/交换复用，不是240独立环境。每例核初态及32末态，不新模拟。

令m_i=raw_i+1(unit_i非空)。`driven.py`和`local.py`保持数组位置与占据；`material.py`死亡使同格占据−1/raw+1，形成使目标占据+1/raw−1、亲本占据不变。`heredity.py`只改材料标签/程序，`hereditary_growing.py`组合上述阶段。因此每次局部转换保持每个m_i，而非仅总和守恒。五个源文件的hash均在401绑定内。单元的材料标签可以变化，守恒的是原料/单元的数量，不是各标签数。

材料支持集布局：

| 位置 | 坐标(x,y) | 初态材料形态 |
|---:|---|---|
| 85 | (5,5) | 原单元0 |
| 86 | (6,5) | 原单元1 |
| 101 | (5,6) | 原料1 |
| 102 | (6,6) | 原料1 |
| 117 | (5,7) | 原料1 |
| 118 | (6,7) | 原料1 |
| 204 | (12,12) | 哨兵单元2 |

前六格组成2×3相邻区域，204是隔离位置。这是材料可存在的位置，不表示这些位置始终有活单元。单元死亡会腾出位置并留下原料，后续仍须同时满足能量、方向、空位、原料和碰撞条件。

## 完整北向票与提案计数

all含哨兵root2，target仅root0/1；消解的北向行动者不计入存活提案。每格20案例、660快照、168960位置检查，偏差全0。供能随机模式四格北向票为0，仍完整保留。

| 程序 | 模式 | 交换 | all票 | all消解 | all提案 | target票 | target消解 | target提案 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 均一 | 方向随机 | False | 902 | 36 | 866 | 744 | 36 | 708 |
| 均一 | 方向随机 | True | 1004 | 0 | 1004 | 846 | 0 | 846 |
| 均一 | 供能随机 | False | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | False | 449 | 29 | 420 | 291 | 29 | 262 |
| 均一 | 双随机 | True | 432 | 23 | 409 | 274 | 23 | 251 |
| 异质 | 方向随机 | False | 915 | 25 | 890 | 757 | 25 | 732 |
| 异质 | 方向随机 | True | 1004 | 0 | 1004 | 846 | 0 | 846 |
| 异质 | 供能随机 | False | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | False | 449 | 29 | 420 | 291 | 29 | 262 |
| 异质 | 双随机 | True | 432 | 23 | 409 | 274 | 23 | 251 |

全部5422条存活北向事件含target4158条；all北向票5587、消解165，target票4323、消解165。all与target差1264条均来自哨兵；两者不是额外独立数据。

## 全部分类、能量和执行分支

类别：无初始材料=no_initial_material、占据=occupied、可用=available、其他=other；定义逐项见协议。能量就绪仅表示形成前能量≥16，不代表可形成。五原因是原执行顺序标签，不能当独立必要因果；每行原因之和等于n。完整零类别/零分支如下。

| 程序 | 模式 | 交换 | 范围 | 类别 | n | 能量就绪 | energy | occupied | raw_material | collision | formed |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 均一 | 方向随机 | False | all | no_initial_material | 468 | 468 | 0 | 0 | 468 | 0 | 0 |
| 均一 | 方向随机 | False | all | occupied | 338 | 197 | 141 | 197 | 0 | 0 | 0 |
| 均一 | 方向随机 | False | all | available | 60 | 60 | 0 | 0 | 0 | 20 | 40 |
| 均一 | 方向随机 | False | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 方向随机 | False | target | no_initial_material | 310 | 310 | 0 | 0 | 310 | 0 | 0 |
| 均一 | 方向随机 | False | target | occupied | 338 | 197 | 141 | 197 | 0 | 0 | 0 |
| 均一 | 方向随机 | False | target | available | 60 | 60 | 0 | 0 | 0 | 20 | 40 |
| 均一 | 方向随机 | False | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 方向随机 | True | all | no_initial_material | 468 | 468 | 0 | 0 | 468 | 0 | 0 |
| 均一 | 方向随机 | True | all | occupied | 536 | 492 | 44 | 492 | 0 | 0 | 0 |
| 均一 | 方向随机 | True | all | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 方向随机 | True | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 方向随机 | True | target | no_initial_material | 310 | 310 | 0 | 0 | 310 | 0 | 0 |
| 均一 | 方向随机 | True | target | occupied | 536 | 492 | 44 | 492 | 0 | 0 | 0 |
| 均一 | 方向随机 | True | target | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 方向随机 | True | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | all | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | all | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | all | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | target | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | target | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | target | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | False | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | all | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | all | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | all | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | target | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | target | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | target | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 供能随机 | True | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | False | all | no_initial_material | 333 | 239 | 94 | 0 | 239 | 0 | 0 |
| 均一 | 双随机 | False | all | occupied | 66 | 15 | 51 | 15 | 0 | 0 | 0 |
| 均一 | 双随机 | False | all | available | 21 | 0 | 21 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | False | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | False | target | no_initial_material | 175 | 81 | 94 | 0 | 81 | 0 | 0 |
| 均一 | 双随机 | False | target | occupied | 66 | 15 | 51 | 15 | 0 | 0 | 0 |
| 均一 | 双随机 | False | target | available | 21 | 0 | 21 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | False | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | True | all | no_initial_material | 316 | 242 | 74 | 0 | 242 | 0 | 0 |
| 均一 | 双随机 | True | all | occupied | 88 | 11 | 77 | 11 | 0 | 0 | 0 |
| 均一 | 双随机 | True | all | available | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | True | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | True | target | no_initial_material | 158 | 84 | 74 | 0 | 84 | 0 | 0 |
| 均一 | 双随机 | True | target | occupied | 88 | 11 | 77 | 11 | 0 | 0 | 0 |
| 均一 | 双随机 | True | target | available | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| 均一 | 双随机 | True | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 方向随机 | False | all | no_initial_material | 468 | 468 | 0 | 0 | 468 | 0 | 0 |
| 异质 | 方向随机 | False | all | occupied | 377 | 232 | 145 | 232 | 0 | 0 | 0 |
| 异质 | 方向随机 | False | all | available | 45 | 45 | 0 | 0 | 0 | 13 | 32 |
| 异质 | 方向随机 | False | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 方向随机 | False | target | no_initial_material | 310 | 310 | 0 | 0 | 310 | 0 | 0 |
| 异质 | 方向随机 | False | target | occupied | 377 | 232 | 145 | 232 | 0 | 0 | 0 |
| 异质 | 方向随机 | False | target | available | 45 | 45 | 0 | 0 | 0 | 13 | 32 |
| 异质 | 方向随机 | False | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 方向随机 | True | all | no_initial_material | 468 | 468 | 0 | 0 | 468 | 0 | 0 |
| 异质 | 方向随机 | True | all | occupied | 536 | 492 | 44 | 492 | 0 | 0 | 0 |
| 异质 | 方向随机 | True | all | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 方向随机 | True | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 方向随机 | True | target | no_initial_material | 310 | 310 | 0 | 0 | 310 | 0 | 0 |
| 异质 | 方向随机 | True | target | occupied | 536 | 492 | 44 | 492 | 0 | 0 | 0 |
| 异质 | 方向随机 | True | target | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 方向随机 | True | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | all | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | all | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | all | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | target | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | target | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | target | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | False | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | all | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | all | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | all | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | target | no_initial_material | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | target | occupied | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | target | available | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 供能随机 | True | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | False | all | no_initial_material | 333 | 239 | 94 | 0 | 239 | 0 | 0 |
| 异质 | 双随机 | False | all | occupied | 66 | 15 | 51 | 15 | 0 | 0 | 0 |
| 异质 | 双随机 | False | all | available | 21 | 0 | 21 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | False | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | False | target | no_initial_material | 175 | 81 | 94 | 0 | 81 | 0 | 0 |
| 异质 | 双随机 | False | target | occupied | 66 | 15 | 51 | 15 | 0 | 0 | 0 |
| 异质 | 双随机 | False | target | available | 21 | 0 | 21 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | False | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | True | all | no_initial_material | 316 | 242 | 74 | 0 | 242 | 0 | 0 |
| 异质 | 双随机 | True | all | occupied | 88 | 11 | 77 | 11 | 0 | 0 | 0 |
| 异质 | 双随机 | True | all | available | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | True | all | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | True | target | no_initial_material | 158 | 84 | 74 | 0 | 84 | 0 | 0 |
| 异质 | 双随机 | True | target | occupied | 88 | 11 | 77 | 11 | 0 | 0 | 0 |
| 异质 | 双随机 | True | target | available | 5 | 0 | 5 | 0 | 0 | 0 | 0 |
| 异质 | 双随机 | True | target | other | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

方向随机/定点供能关闭交换时，均一有60次可用目标且能量就绪（20碰撞、40形成），异质45次（13碰撞、32形成）；开启交换可用目标均0。双随机可用目标关闭21、开启5，各程序相同且均能量不足。此为完整既有事件分解，不是改变某条件后的干预效应。

## 证据与核验

- 正式提交`79e8159ca7aa1c42660ad1e5e494fcc8f1b12a32`，直接审计4.251885秒；独立字典重放全部7680保存步并审计10.096390秒，均在300秒预算内。
- 401来源/代码绑定前后相同，三输出hash与核验脚本hash通过；完整四根JSON1,350,295字节逐字节归档，低于64MiB。
- [metadata](results/v4-study-033-metadata.json)、[全部240案例与5422事件](results/v4-study-033-records.json)、[12格完整摘要](results/v4-study-033-summary.json)、[独立核验](results/v4-study-033-independent-verification.json)。原始240轨迹继续由019/023/025归档及026证据链绑定，不复制或覆盖旧数据。
- 最终766测试PASS（51.427秒）、编译与代码审查通过；同总量材料跨格转移会产生两条偏差，测试防止只验总和；输入类型/顺序/类别、部分进度、失败哈希、独占输出和预算有反例。
- 生产/独立物理核验由两个新上下文作者实现；第三审查代理触及数量限制，代码与报告审查如实为inline fallback，不冒称第三独立作者。修正过读取旧026proof格式的兼容问题，前后输入由metadata保存，proof绑定其hash，旧证据未变。
- 0新增实验模拟步、环境、初始世界；原生命标准未调整，不能把可用位置或局部形成等同自主结构复制。

## 下一步

先冻结固定支持集内原始两成员模板的全部可容纳平移位置，再核查240保存轨迹中这些位置的实际身份/祖链、连接与组件边界。这样区分“空间上可放下”与“实际形成独立副本”，不添加材料迁移、供能或新的初态，不因空间限制直接放宽生命标准。

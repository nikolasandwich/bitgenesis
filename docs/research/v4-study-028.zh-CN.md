# Study028：一次补能形成后的固定窗口延续

全部52个新增单元均在原第32步前消解，没有再繁殖、没有后代留存；所有处理与对照的连续10步遗传双副本均为零。每个处理分支末态的单元与原料数组都回到其原轨迹对照末态，仅原哨兵身份2存活。027的单阶段形成成功没有转化为本窗口内的持续后果。

## 固定方法与分母

[协议](../../experiments/v4/study-028.md)于699dce6冻结；正式执行提交`9e4c08a6032f45031dc94a322cc527476fa31d37`。接续027全52处理阶段终态，原方向、供能提议和突变票继续至原第32步，不再补能、不延长观察。共996新完整世界步、0新实验形成阶段重做；复用20来源筛选证明，实际入选11seed、26个程序/交换案例臂。每条延续10–26步，52个事件状态不是52独立来源，不作显著性检验。

各分支保留干预前身份，新生及未来身份按自身事件顺序重建，不沿用原轨迹未来身份。对照读取原保存轨迹；新增单元出生于已保存027阶段，本轮births/deaths/imported/spent仅计tick+1到32。遗传与材料双副本指标仍观察完整1–32步并使用原模板、原完整组件定义；共同前缀也计入，不能将“曾有”误说成干预后的新出现。

## 新增单元命运：完整四格

| 程序 | 交换 | 分支数 | 第32步自身存活 | 曾再繁殖 | 第32步谱系存活 | final存活观测次数范围 | 次数合计 |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| homogeneous | 关 | 21 | 0 | 0 | 0 | 2–9 | 64 |
| homogeneous | 开 | 5 | 0 | 0 | 0 | 3–10 | 26 |
| heterogeneous | 关 | 21 | 0 | 0 | 0 | 5–13 | 129 |
| heterogeneous | 开 | 5 | 0 | 0 | 0 | 5–13 | 49 |

final存活观测包括形成当步，等于消解tick−形成tick；不能把它当独立重复样本数。所有death_tick均实测，右删失0；所有direct_offspring、descendants_born和lineage_living_final均0。异质两格的观测存活次数合计较高，但没有跨过再繁殖或窗口末存活门槛。

## 全部10项指标与反向结果

下表是状态加权合计，同一旧案例可被多个干预状态重复使用；不是11来源等权均值。正/负/零是52分支内逐项处理−对照的方向，不是好坏评价。births不包含已在027完成的那个新增单元；每分支后续deaths恰好多1，后续births差均0。末能量和存活人数逐分支差均0。

| 程序 | 交换 | 指标 | 原对照合计 | 处理合计 | 差 | 正/负/零分支 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| homogeneous | 关 | births | 5 | 5 | 0 | 0/0/21 |
| homogeneous | 关 | deaths | 68 | 89 | 21 | 21/0/0 |
| homogeneous | 关 | living | 21 | 21 | 0 | 0/0/21 |
| homogeneous | 关 | final_energy | 728 | 728 | 0 | 0/0/21 |
| homogeneous | 关 | imported | 80 | 104 | 24 | 3/0/18 |
| homogeneous | 关 | spent | 1048 | 1218 | 170 | 19/2/0 |
| homogeneous | 关 | genetic_ever | 1 | 0 | -1 | 0/1/20 |
| homogeneous | 关 | genetic_persistent10 | 0 | 0 | 0 | 0/0/21 |
| homogeneous | 关 | longest_genetic | 1 | 0 | -1 | 0/1/20 |
| homogeneous | 关 | material_ever | 1 | 0 | -1 | 0/1/20 |
| homogeneous | 开 | births | 0 | 0 | 0 | 0/0/5 |
| homogeneous | 开 | deaths | 13 | 18 | 5 | 5/0/0 |
| homogeneous | 开 | living | 5 | 5 | 0 | 0/0/5 |
| homogeneous | 开 | final_energy | 160 | 160 | 0 | 0/0/5 |
| homogeneous | 开 | imported | 0 | 16 | 16 | 2/0/3 |
| homogeneous | 开 | spent | 215 | 256 | 41 | 4/0/1 |
| homogeneous | 开 | genetic_ever | 0 | 0 | 0 | 0/0/5 |
| homogeneous | 开 | genetic_persistent10 | 0 | 0 | 0 | 0/0/5 |
| homogeneous | 开 | longest_genetic | 0 | 0 | 0 | 0/0/5 |
| homogeneous | 开 | material_ever | 0 | 0 | 0 | 0/0/5 |
| heterogeneous | 关 | births | 5 | 5 | 0 | 0/0/21 |
| heterogeneous | 关 | deaths | 68 | 89 | 21 | 21/0/0 |
| heterogeneous | 关 | living | 21 | 21 | 0 | 0/0/21 |
| heterogeneous | 关 | final_energy | 728 | 728 | 0 | 0/0/21 |
| heterogeneous | 关 | imported | 80 | 136 | 56 | 7/0/14 |
| heterogeneous | 关 | spent | 1048 | 1250 | 202 | 19/2/0 |
| heterogeneous | 关 | genetic_ever | 1 | 1 | 0 | 0/0/21 |
| heterogeneous | 关 | genetic_persistent10 | 0 | 0 | 0 | 0/0/21 |
| heterogeneous | 关 | longest_genetic | 1 | 1 | 0 | 0/0/21 |
| heterogeneous | 关 | material_ever | 1 | 1 | 0 | 0/0/21 |
| heterogeneous | 开 | births | 0 | 0 | 0 | 0/0/5 |
| heterogeneous | 开 | deaths | 13 | 18 | 5 | 5/0/0 |
| heterogeneous | 开 | living | 5 | 5 | 0 | 0/0/5 |
| heterogeneous | 开 | final_energy | 160 | 160 | 0 | 0/0/5 |
| heterogeneous | 开 | imported | 0 | 24 | 24 | 3/0/2 |
| heterogeneous | 开 | spent | 215 | 264 | 49 | 4/0/1 |
| heterogeneous | 开 | genetic_ever | 0 | 0 | 0 | 0/0/5 |
| heterogeneous | 开 | genetic_persistent10 | 0 | 0 | 0 | 0/0/5 |
| heterogeneous | 开 | longest_genetic | 0 | 0 | 0 | 0/0/5 |
| heterogeneous | 开 | material_ever | 0 | 0 | 0 | 0/0/5 |

一次反向事件：均一程序、交换关闭、seed120019、tick7、site118、原身份5。原对照在7–7步有双副本，补能新增身份7占据site102且材料为0后，材料组件成为[0,1,5,6,7]，全程不再有双副本。异质对应状态的新生材料为2，材料组件仍分为[0,1]、[5,6]、[7]及哨兵[2]，保留7–7的一步匹配。均一新生tick10消解，异质tick12消解，二者均未再繁殖；这不支持持续复制。组件是材料连通定义，不能混称当步实际能量连接。

后续四格接受能量差为+24/+16/+56/+24，支出差为+170/+41/+202/+49；它们分别与027处理阶段末能量差+146/+25/+146/+25抵消，末态能量差均0。全部合计342+120−462=0。602历史外能已有260在027额外形成成本中支出，不能在本轮再加一次。不同吸收量说明必须重用环境proposed并重新计算accepted。

## 全52分支命运

所有分支均无再繁殖、无后代；表保留每次形成和死亡时刻，不删阴性。身份仅在各分支内有效。

| 分支 | 程序 | 交换 | seed | 形成tick | source site | 原父身份 | 新生身份 | 消解tick | final存活次数 | 遗传最长：对照→处理 |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | homogeneous | 关 | 120001 | 15 | 117 | 6 | 7 | 18 | 3 | 0→0 |
| 1 | homogeneous | 关 | 120005 | 6 | 118 | 4 | 6 | 8 | 2 | 0→0 |
| 2 | homogeneous | 关 | 120005 | 7 | 118 | 4 | 6 | 9 | 2 | 0→0 |
| 3 | homogeneous | 关 | 120005 | 11 | 117 | 6 | 7 | 14 | 3 | 0→0 |
| 4 | homogeneous | 关 | 120006 | 10 | 117 | 6 | 7 | 13 | 3 | 0→0 |
| 5 | homogeneous | 关 | 120008 | 13 | 118 | 6 | 7 | 16 | 3 | 0→0 |
| 6 | homogeneous | 关 | 120010 | 22 | 102 | 5 | 6 | 25 | 3 | 0→0 |
| 7 | homogeneous | 关 | 120011 | 13 | 117 | 6 | 7 | 16 | 3 | 0→0 |
| 8 | homogeneous | 关 | 120012 | 13 | 102 | 4 | 5 | 16 | 3 | 0→0 |
| 9 | homogeneous | 关 | 120012 | 16 | 102 | 4 | 5 | 19 | 3 | 0→0 |
| 10 | homogeneous | 关 | 120013 | 8 | 117 | 5 | 6 | 10 | 2 | 0→0 |
| 11 | homogeneous | 关 | 120015 | 7 | 117 | 5 | 6 | 9 | 2 | 0→0 |
| 12 | homogeneous | 关 | 120015 | 9 | 117 | 5 | 6 | 11 | 2 | 0→0 |
| 13 | homogeneous | 关 | 120015 | 16 | 102 | 4 | 6 | 19 | 3 | 0→0 |
| 14 | homogeneous | 关 | 120017 | 9 | 117 | 4 | 5 | 12 | 3 | 0→0 |
| 15 | homogeneous | 关 | 120017 | 11 | 117 | 4 | 5 | 14 | 3 | 0→0 |
| 16 | homogeneous | 关 | 120017 | 13 | 117 | 4 | 5 | 16 | 3 | 0→0 |
| 17 | homogeneous | 关 | 120017 | 16 | 117 | 4 | 6 | 19 | 3 | 0→0 |
| 18 | homogeneous | 关 | 120017 | 19 | 117 | 4 | 6 | 28 | 9 | 0→0 |
| 19 | homogeneous | 关 | 120017 | 22 | 117 | 4 | 6 | 25 | 3 | 0→0 |
| 20 | homogeneous | 关 | 120019 | 7 | 118 | 5 | 7 | 10 | 3 | 1→0 |
| 21 | homogeneous | 开 | 120006 | 12 | 101 | 5 | 6 | 19 | 7 | 0→0 |
| 22 | homogeneous | 开 | 120017 | 11 | 117 | 4 | 5 | 14 | 3 | 0→0 |
| 23 | homogeneous | 开 | 120017 | 13 | 117 | 4 | 5 | 16 | 3 | 0→0 |
| 24 | homogeneous | 开 | 120017 | 16 | 117 | 4 | 5 | 19 | 3 | 0→0 |
| 25 | homogeneous | 开 | 120017 | 19 | 117 | 4 | 5 | 29 | 10 | 0→0 |
| 26 | heterogeneous | 关 | 120001 | 15 | 117 | 6 | 7 | 20 | 5 | 0→0 |
| 27 | heterogeneous | 关 | 120005 | 6 | 118 | 4 | 6 | 11 | 5 | 0→0 |
| 28 | heterogeneous | 关 | 120005 | 7 | 118 | 4 | 6 | 12 | 5 | 0→0 |
| 29 | heterogeneous | 关 | 120005 | 11 | 117 | 6 | 7 | 16 | 5 | 0→0 |
| 30 | heterogeneous | 关 | 120006 | 10 | 117 | 6 | 7 | 15 | 5 | 0→0 |
| 31 | heterogeneous | 关 | 120008 | 13 | 118 | 6 | 7 | 18 | 5 | 0→0 |
| 32 | heterogeneous | 关 | 120010 | 22 | 102 | 5 | 6 | 27 | 5 | 0→0 |
| 33 | heterogeneous | 关 | 120011 | 13 | 117 | 6 | 7 | 18 | 5 | 0→0 |
| 34 | heterogeneous | 关 | 120012 | 13 | 102 | 4 | 5 | 18 | 5 | 0→0 |
| 35 | heterogeneous | 关 | 120012 | 16 | 102 | 4 | 5 | 29 | 13 | 0→0 |
| 36 | heterogeneous | 关 | 120013 | 8 | 117 | 5 | 6 | 13 | 5 | 0→0 |
| 37 | heterogeneous | 关 | 120015 | 7 | 117 | 5 | 6 | 12 | 5 | 0→0 |
| 38 | heterogeneous | 关 | 120015 | 9 | 117 | 5 | 6 | 14 | 5 | 0→0 |
| 39 | heterogeneous | 关 | 120015 | 16 | 102 | 4 | 6 | 21 | 5 | 0→0 |
| 40 | heterogeneous | 关 | 120017 | 9 | 117 | 4 | 5 | 14 | 5 | 0→0 |
| 41 | heterogeneous | 关 | 120017 | 11 | 117 | 4 | 5 | 16 | 5 | 0→0 |
| 42 | heterogeneous | 关 | 120017 | 13 | 117 | 4 | 5 | 18 | 5 | 0→0 |
| 43 | heterogeneous | 关 | 120017 | 16 | 117 | 4 | 6 | 29 | 13 | 0→0 |
| 44 | heterogeneous | 关 | 120017 | 19 | 117 | 4 | 6 | 32 | 13 | 0→0 |
| 45 | heterogeneous | 关 | 120017 | 22 | 117 | 4 | 6 | 27 | 5 | 0→0 |
| 46 | heterogeneous | 关 | 120019 | 7 | 118 | 5 | 7 | 12 | 5 | 1→1 |
| 47 | heterogeneous | 开 | 120006 | 12 | 101 | 5 | 6 | 25 | 13 | 0→0 |
| 48 | heterogeneous | 开 | 120017 | 11 | 117 | 4 | 5 | 16 | 5 | 0→0 |
| 49 | heterogeneous | 开 | 120017 | 13 | 117 | 4 | 5 | 18 | 5 | 0→0 |
| 50 | heterogeneous | 开 | 120017 | 16 | 117 | 4 | 5 | 29 | 13 | 0→0 |
| 51 | heterogeneous | 开 | 120017 | 19 | 117 | 4 | 5 | 32 | 13 | 0→0 |

## 核验与可恢复档案

688测试PASS50.043秒；生产3.965930秒，独立核验3.254338秒。413来源/代码绑定前后一致，全部52完整分支、996物理步、组件、身份、复制匹配、命运与汇总逐字段核验，55输出hash绑定。预算600秒/128MiB。

原生生产与字典核验由两个新上下文作者独立实现；使用既有的不同物理、身份及匹配路线。第三个审查任务受工具数量限制，代码与报告审查为主上下文inline fallback，不称第三位独立作者审查。全量正式处理只执行一次；工程验证只用少量固定分支fixture。

52个完整分支原始25,461,034字节，压缩497,469字节。已实际解压到空临时目录，52个成员逐文件大小和SHA256一致。根四JSON也逐字节归档。

- [metadata.json](results/v4-study-028-metadata.json)：SHA256 `a9a8d7a9fb2e15bf8ad6caf719cb3f5326cf108b6c38bdf327a01e440c924fbc`。
- [records.json](results/v4-study-028-records.json)：SHA256 `37217906040aa2a6e945849be96f5883cf8f4fe43ce9c5624fada69f90e0bfcd`。
- [summary.json](results/v4-study-028-summary.json)：SHA256 `071a95039f1e69e9c07f2f7c1fb8d94a7a991630200da1b03c15638b01478b79`。
- [independent-verification.json](results/v4-study-028-independent-verification.json)：SHA256 `e8dd6ba00b768b2f08c79c76fe3fde7b4d9514123455a93b626a6e062d919ba2`。
- [cases.tar.gz](results/v4-study-028-cases.tar.gz)：SHA256 `6126d625324535c8cb22b2d573f314fe5f3baa79eda1cadac22736336d92ae19`。
- [archive-verification.json](results/v4-study-028-archive-verification.json)：SHA256 `cefdee1000b00f5e78e1f147e3305c0f2d72d57146280afc62774fde153a223b`。

## 接续问题

本轮仅排除了这一固定筛定集合、一次性补能和原32步窗口内的持续收益，不证明任何环境下都不可能。原生命标准、自然来源阴性与构造对照的限定范围均不改变。

下一轮优先只读这52份新轨迹，先冻结新增单元从形成到消解的逐步能量账本：实际吸收、泄漏、连接成本、交换净流、以及任何形成支出分别核对，并在对应26对均一/异质状态中完整比较。保留全部死亡和没有吸收的个案，检查较长存活与哪些账目同时出现；账目解释不冒称单因素必要因果，不先追加供能或延长观察去追求阳性。

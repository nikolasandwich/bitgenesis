# Study037：移除原组后上行再形成的障碍与组件转换

## 1 问题与固定范围

仅审计036全20个random-direction处理分支（均一11、异质9，全部交换关闭），包含8个短窗口，不挑阳性；共274个未来末态，另20个t0+仅作转换基线。其他38处理分支和182未入选由036来源保留，不归入本队列分母。0新增或重放物理步，不延时、不新增环境、规则或生命标准。

固定问题：上行85/86能否同时占据、匹配原材料/完整程序、形成完整材料组件，及其成员是否确由选中下行副本祖系在处理后形成？何时上行合格组件和双全新组件出现/消失，伴随哪些出生、消解与中行连接？不同程序t0不同，不当单因素程序效应；先失败层是描述顺序，不是独立因果贡献。

## 2 方法与字段

对t0+及未来每末态，固定三槽85/86、101/102、117/118，从原始单元、身份历史及材料组件独立计算occupied、material_match、genetic_match、whole_component、root_descendant、all_new、post_birth（两成员birth_tick>t0）、selected_ancestry（两成员均追到所选下行成员之一）八谓词。缺任一成员则八谓词全false。genetic_match含material_match；root_descendant指根0/1；copy=genetic_match且whole_component且root_descendant，new_copy另需all_new。post_birth与selected_ancestry分开，不偷换原复制定义。记录每槽身份、完整程序、材料、出生时点、选中祖先链及成员所属完整组件；t0+不计分母/持续区间。

上行first_failure顺序：missing、material、program、component、ancestry_root、original_member、pass。保留所有八独立谓词及零计数，不将首失败当唯一阻碍。上行成员所在材料组件与中行101/102交集另列connector_sites，不能将材料几何连接称实际能量交换bond。

逐步记录出生/自然死亡身份、位置、材料及程序；保留t0+作为前态，列upper_new_copy和double_new（new_copy数>=2）的每个进入/退出事件，附前后谓词、连接位置与当步出生死亡。没有变动不伪造事件，窗口终点仍为true标右删失，不假造退出。每例计算未来upper_new_copy、upper_selected_post_copy（upper_new_copy且post_birth且selected_ancestry）、double_new区间及最长连续步数，10步阈值不变。和036的全部未来new_copy_counts及double episodes逐例对照。

## 3 核验、预算与交付

先冻结协议/规格再实现。生产使用保存原始状态与既有snapshot，独立作者用pairwise union-find组件重建、独立父链追溯与直接两点模板比较；不得导入生产科学计算。不重算物理。核验全部20例/274行，不预设事件数，事件总数据正式运行报告；三槽观察数为822（不含60个诊断槽）。工程仅首入选方向案例，正式全队列只运行一次。

每路线600秒、输出128MiB，独占data/v4-study-037不覆盖；来源绑定036原始分支与证明、035选择及旧代码链，保留全部阴性、前后hash、独立证明，根JSON逐字节归档。边界测试覆盖程序错配与组件合并区分、身份/祖系、诊断排除、右删失、无事件和10步阈值。完成报告/日志/规格并提交推送。第三审查如受限标inline fallback，不冒称独立作者。

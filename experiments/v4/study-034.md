# Study034：固定支持内模板位置与真实组件

## 1 范围与几何

只读033已绑定240案例/7680末态步，沿genotype homogeneous/heterogeneous→mode random-direction/random-feed/random-both→exchange False/True→seed120000..120019顺序。初始模板是site85/86的两成员及其材料/完整程序，原身份0/1。材料支持从初态raw+占据>0导出。枚举16×16周期平移，不旋转，不按观察结果筛位置；所有模板位置须完全位于支持。固定初态应得到[[85,86],[101,102],[117,118]]（左到右对应模板），按左site升序。三位置互不重叠；几何可容纳不表示占满、独立组件或遗传复制。

0新实验模拟/环境/初态，不改规则。只核final材料邻接组件，非interaction实际能量承担的bond图；whole_component要求完整material组件恰是两个身份，不能从大组件裁子集。

## 2 两路线及输出

生产scripts/analyze_v4_copy_slots.py placements(support)→list，枚举全部周期平移；analyze_case(case,genotype)读保存final observation及身份/祖链，输出record；独立scripts/verify_v4_copy_slots.py同接口，placements用支持内有序邻接对几何判定；analyze_case先旧verify_v4_north_opportunities.recount全字典物理重放，再structure_audit.reconstruct独立重建initial/每final材料组件且等于保存observation，不读取新生产。可复用旧require/same，不能共享新科学计算。

record键genotype,mode,exchange,seed,placements,rows,episodes,longest。rows长度32，每项tick,slots,copy_count,new_copy_count。每slots长度3，按placements顺序，每项sites,identities,roots（两元素list，可None），occupied,material_match,genetic_match,whole_component,descendant,all_new,copy,new_copy（全bool）。occupied两位置均非空；material_match两位置分别等于模板material；genetic_match再分别完整program相等；whole_component=occupied且排序identities恰等于一个完整final material组件；descendant=occupied且roots都在0/1；all_new=occupied且identities都不在0/1；copy=genetic_match且whole_component且descendant；new_copy=copy且all_new。缺任一单元时上述所有bool均False。roots沿final.parents追溯原0/1/2，身份不替换复用。数组含位置原顺序，不按身份排序。

episodes是copy_count>=2的所有闭区间[start,end]，longest为最大长度(空0)。原连续10步标准保持；不是同一pair成员持续标准。sum(new_copy)>=2另记新生成双副本步，不把原组算新生。不得声称新生副本有进一步繁殖。

summarize(records)→12格list：genotype,mode,exchange,n20,saved_steps640,slot_steps1920,totals（八bool字段各累计）,slots（3项，每项sites和相同八bool字段累计）,double_steps,new_double_steps,triple_steps,cases_ever_double,cases_persistent10,max_double_run。核完整有序240、所有schema/type/count/布尔关系、episodes与longest重算；全零保留。若copy_count与旧017/019等观察不一致，先解释/修复，不改标准。

## 3 证据与预算

helper scripts/copy_slots_inputs.py继承033的401绑定，加033四根/四归档8与本协议/三新脚本4，共413；source_cases/read/save/digest/input_paths(errors)/bindings，仅IO。核033 complete240/7680/7920/2027520、proof verified401、前后绑定、三输出hash、自身verifierhash和四归档。失败保留可读hash/输入读错。

独占data/v4-study-034，clean launch；300秒/64MiB，逐case保存records/metadata，最终写后复查。metadata字段同033但移除checked_snapshots/checked_sites，改slot_steps=96*completed_cases，其余planned_cases240,completed_cases,saved_steps32*n,new_simulation_steps0,new_environment_sources0,reused_environment_sources20,new_independent_initial_worlds0,time_limit_seconds300,storage_limit_bytes67108864,status,git_commit,elapsed_seconds,input_paths,input_sha256,input_sha256_after,output_sha256，可选成功空inventory/read errors。proof核413输入、240记录/7680步/23040slot_steps、完整summary和三输出hash、自身hash、前后输入、独占/预算/失败证据。

先TDD、审查、小fixture及至多同一首真实案例（homogeneous/random-direction/False/120000）；工程不全240预跑。干净提交正式运行，四JSON完整逐字节归档。持续授权intentional fast-track。第三新审查不可用如实inline fallback；不冒称独立作者。

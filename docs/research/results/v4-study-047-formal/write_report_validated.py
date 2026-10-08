"""Write the formal author report from frozen audit, summary and archive evidence."""
from pathlib import Path
import hashlib,json
R=Path('/Users/todd/Documents/bitgenesis');B=R/'data/v4-study-047';D=R/'docs/research/results/v4-study-047-formal'
a=json.loads((B/'audit.json').read_bytes());x=json.loads((B/'report-analysis.json').read_bytes());z=json.loads((D/'archive-manifest.json').read_bytes());s=a['summary'];names={'east':'E','west':'W','south':'S','north':'N','homogeneous':'H'};arms=('continue_north','withdraw_to_natural')
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(('null' if v is None else str(v)) for v in row)+' |' for row in rows])
def interval(v):return '；'.join((str(i['start']) if i['start']==i['end'] else f"{i['start']}–{i['end']}")+(' L' if i['left_censored_at_boundary'] else '')+(' R' if i['right_censored'] else '') for i in v) or '无'
lines=['# Study047：既定北向前缀后的方向控制撤除结果','',
'2026-10-09。全部28个既定tick32终态的两臂正式后缀已实际运行；生产与独立字典物理核验各执行一次、各1792步并成功。完整45科学对象严格具体类型、值与各自原始字节一致。固定33–64窗口内，两臂的future_persistent10均为0/28；这是有限窗口内主终点未达到，不是撤除无效或未来不可能持续。',
'',
'作者交付状态为 **READY_FOR_REVIEW**，报告交付后冻结。已发现两CLI既有进程门禁对macOS大写Python解释器漏检；其范围、启动前父层辅助证据及限制在下文单列。独立正式审查及父层规格最终验收尚未完成，本报告不宣称任务3.1最终完成或FEATURE_GO。',
'', '## 固定问题与队列', '',
'估计对象是043已接受北向政策并在原t0移除创始0/1的全部28个分支，分别从同一 `/ablation/final` tick32终态继续101/102北向方向3，或撤除该覆盖、使用全256自然方向。同seed跨编码和两臂共享自然票，其他规则、固定外部供能、原模板、完整组件/四项程序/材料/祖系标准不变。差值固定为withdraw_to_natural−continue_north。方向还决定程序材料表达，不能拆称纯机会或能量效应。',
'',
'原100索引全部保留；72个原32步未触发分支为N/A、future=null，没有047后缀，不能称为100例64步阴性。E/W/S/N/H依次代表east/west/south/north/homogeneous，纳入数5/3/0/9/11。全28配对属于14个共享环境seed，不是28个独立环境，也没有显著性检验。10个原短窗标签保留，但全部纳入分支本次都有32个未来末态。工程E120005再次作为正式队列一员运行，工程数据未混入或替代正式一例。',
'',
'运行前问题、方案、固定全队列与验收标准见[task brief](results/v4-study-047-formal/raw/task-brief.zh-CN.md)；科学预注册见[study-047](../../experiments/v4/study-047.md)。tick32仅诊断，主终点严格使用33–64未来q(t)≥2连续至少10末态；不借过去长度满足未来10。',
'', '## 实际执行、预算与来源', '',
'从已推送的干净工程提交 `a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f` 执行。运行前逐项核实生产1985、核验3023、工程3535审批绑定；两路线前后HEAD、origin/main与全部Git跟踪文件一致。两CLI完成前只写Git忽略的独占data目录，正式报告及归档随后创建。准确argv、完整显式子环境、cwd、开始/结束时间、exit、原始stdout/stderr和源码前后hash见[生产执行](results/v4-study-047-formal/raw/execution/producer/request.json)及[核验执行](results/v4-study-047-formal/raw/execution/verifier/request.json)。子进程仅传PATH、HOME、TMPDIR、LANG（父环境存在时）及PYTHONPATH=src，没有继承其他环境变量。',
'', '```text','PYTHONPATH=src .venv/bin/python scripts/run_v4_middle_withdrawal.py --mode formal --output data/v4-study-047/producer','PYTHONPATH=src .venv/bin/python scripts/verify_v4_middle_withdrawal.py --mode formal --producer data/v4-study-047/producer --output data/v4-study-047/verifier','```','']
rows=[]
for label,key in [('CLI退出码',None),('metadata状态','status'),('包装器墙时（秒）','wall_seconds'),('metadata内部耗时（秒）','metadata_elapsed_seconds'),('真实未来物理步','physical_steps'),('未来生成器tick','future_generator_ticks'),('过去生成器重建tick','past_generator_ticks'),('前后及当前一致输入项数','input_bindings_verified'),('最终路线文件大小（字节）','actual_route_bytes')]:rows.append([label]+[0 if key is None else a['routes'][r][key] for r in ['producer','verifier']])
lines+=[table(['项目','生产','独立核验'],rows),'',
'两路线均在原600秒/134217728字节硬限内，均完整完成28对；没有真实失败运行、重试、选窗、缩队列或删科学字段。每路线448未来生成器tick=14seed×32、114688方向值；过去640tick=20seed×32只恢复原随机消费，不重放物理。正式共3584物理步，已完成工程128步单列，实际累计与原计划一致为3712。工程两路线未来各32生成器tick；正式两路线各448，合计960未来生成器tick（不计既有合成测试）。本轮新增合成物理/未来票均0。',
'',
'生产1195输入=1192冻结闭包+三份审批；核验1241输入再绑定全部46份生产输出。前后及当前hash逐项一致，完整输入清单和读取/收尾错误空表见两路线metadata及核验proof。201份源码、测试和执行合同原字节快照保留。科学算法分别由已审查生产/独立核验作者实现，本轮两命令由同一实施者操作；不把核验当新增科学样本。',
'', '## 完整对象与状态、政策、账核查', '',
f"[只读审计](results/v4-study-047-formal/raw/audit.json)比较28case、14environment、records/index/summary共45份完整对象、{x['complete_scientific_object_nodes']}个节点，逐层要求相同具体类型和值；拒绝0/False或8/8.0混同。本次45份科学文件各自原字节也相同。全部自审包含来源、账与统计复核共{a['strict_comparison_nodes']}节点，执行exit0、wall7.789679375011474秒。metadata与proof是各自执行证据，分别保存自身原字节，不声称相同。",
'',
'每对边界引用按path/pointer/文件hash/规范化对象hash解引用，两臂initial均与原043终态严格相同，原source.initial模板及removals旁账完整绑定。活着只取site_ids，历史0/1仍保留且death_tick=None不表示存活；未来新ID接续历史，不重新移除或导出能量。所有56arm的32行、每步方向/固定供能/突变票、质量7、能量收支、连续身份与出生/死亡、组件全部程序及双出生阈值见证均核对。',
'',
f"继续路线101/102合计1792位置×tick无条件北向覆盖，其中{a['policy_overrides_different_from_natural']}项自然票不是3；{a['policy_target_ticks_empty_at_start']}项步初为空也照样执行政策。撤除路线全部256方向逐值等于自然票。这些计数不代表同量的实际提议变化。",
'', '## 主终点、五编码与完整二元四格', '',
'future_persistent10：继续0/28，撤除0/28，28个主配对差全0；未观测到撤除造成主终点增益或损失。最长单臂连续双副本仍为5步，两臂都没有达到10。不能由同为0推出等效性或无政策影响。', '']
rows=[]
for c in s['cells']:
 vals=[c['encoding'],c['n']]
 for k in ['future_persistent10','new_copy_ever','double_new_ever','after32_formation_supported']:vals.append(f"{c['arm_totals'][arms[0]][k]} → {c['arm_totals'][arms[1]][k]}")
 vals.append(c['mean_delta']['future_persistent10']);rows.append(vals)
lines +=[table(['编码','配对数','未来持续10','新副本ever','双副本ever','32后形成支持','主差均值'],rows),'',
'S的零分母均值为null，不能写为零效应；表中的0是保存的计数。其余四编码主差均值为0。全部五格的所有指标、正/负/平数、完整分母和null见[summary](results/v4-study-047-formal/raw/producer/summary.json)。', '']
rows=[]
for k,v in s['overall']['binary_pairs'].items():rows.append([k]+[i['n'] for i in v])
lines +=[table(['二元指标','继续0/撤除0','继续0/撤除1','继续1/撤除0','继续1/撤除1'],rows),'',
'new_copy_ever为19→20，double_new_ever为8→9；原t0后形成支持为8→9，32后形成支持为1→2。新增的ever配对均为H120015，但其双副本观察仅触达终点64，需保留右删失。after32_selected_ancestry_supported等零项也保留，不把一般后代出生与指定祖系支持混为一谈。',
'', '## 全28配对、区间与删失', '',
'下表每行是一个固定配对；L表示接入边界时已连续，R表示到64仍合格。单个数字表示仅该保存末态合格；“无”不是缺失。所有行的未来持续10配对差均0。Δ列均为撤除−继续；完整28指标差及q全32序列、全部组件/成员/出生见证保存在[records](results/v4-study-047-formal/raw/producer/records.json)与所指case，不只保留本表选列。', '']
rows=[]
for p in a['pairs']:
 c=p['arms'][arms[0]];w=p['arms'][arms[1]];d=p['delta'];rows.append([names[p['encoding']]+str(p['seed']),c['q32'],interval(c['intervals']),interval(w['intervals']),d['longest_double'],d['births'],d['deaths'],d['final_energy']])
lines +=[table(['配对','q32','继续双副本区间','撤除双副本区间','Δ最长','Δ出生','Δ自然死亡','Δ末能量'],rows),'',
'继续有13段双副本区间、合计24个合格未来末态，20臂无双副本；撤除有15段、合计28个合格未来末态，19臂无双副本。这些是区间/末态计数，不是额外独立样本。两臂各3段左删失、各3条cross_boundary；右删失仅撤除1段。',
'',
'E/W/H120009是仅有的q32≥2分支，均q32=2，原前缀末段[32,32]与未来[33,34]相接：prefix_length=1、future_length=2、combined_observed_length=3。两臂均如此，原干预边界左删失=false，未来左删失=true，未来右删失=false；combined_persistent10=false。过去1步和诊断tick32没有进入未来主终点。其他分支cross_boundary=null。',
'',
'H120003在继续中仅[33,33]，撤除多出[39,39]；最长与双副本ever都未变，仍不能说完整区间相同。H120011继续仅tick63、撤除49–51，最长1→3，均不持续10；同一出生见证14@35（parent13，site85）在不同合格时段被观察，不是tick49或63才出生。H120015继续没有新副本ever，撤除只在tick64出现两完整新副本，成员[5,7]与[13,15]，见证15@33（parent13，site85）满足32后出生。该[64,64]为右删失：只观察到1个合格末态，不能声称区间已结束、将来不持续或已达到持续标准。',
'',
'完整q序列有9对差异：E120011、W120003、N120003/N120009/N120011/N120018、H120003/H120011/H120015；双副本区间发生变化的是上述3个H分支。18对至少一个记录指标发生变化。其余记录指标差为0也不能保证全部物理过程相同；如E120005主指标相同仍有失败原因分配差异。具体差异tick和全配对列表见[报告数据](results/v4-study-047-formal/raw/report-analysis.json)。',
'', '## 14个共享环境组', '',
'按seed保留编码关联，以下是描述性组内合计；每组主终点配对差都0。不能把同seed不同编码当独立环境，也不从其中3个旧终点阳性选主分母。', '']
lines +=[table(['seed','纳入编码','配对数','ΣΔ最长','ΣΔ末能量'],[[g['seed'],'/'.join(names[e] for e in g['selected_encodings']),g['n'],g['delta_totals']['longest_double'],g['delta_totals']['final_energy']] for g in s['seed_groups']]),'', '## 完整能量、人口与失败账', '']
metric_labels=[('births','未来出生'),('deaths','未来自然死亡'),('living','最终活着'),('imported','接受供能'),('rejected_import','拒绝供能'),('leakage','漏损'),('bond_spent','连接支出'),('construction_spent','构造支出'),('copy_spent','复制支出'),('spent','总支出'),('final_energy','末能量')]
lines +=[table(['跨28分支合计','继续','撤除','差'],[[label,s['overall']['arm_totals'][arms[0]][k],s['overall']['arm_totals'][arms[1]][k],s['overall']['delta_totals'][k]] for k,label in metric_labels]),'',
'两臂共同E32合计6590：继续6590+15014−14601=7003；撤除6590+14809−14388=7011。固定总提议供能各28672，接受+拒绝分别闭合；不能只看末能量+8便称撤除增加能量输入，实际接受输入−205且支出−213。初始活着合计168，继续168+167−178=157、撤除168+182−191=159。每个世界质量全程7，未来export=0；历史移除export只作前缀旁账，不重复扣除，不计自然死亡。', '']
keys=['formed','collision','energy','occupied','raw_material']
lines +=[table(['提议首结果计数','继续','撤除','差'],[[k,x['arm_window_counts'][arms[0]]['failure_counts'][k],x['arm_window_counts'][arms[1]]['failure_counts'][k],x['arm_window_counts'][arms[1]]['failure_counts'][k]-x['arm_window_counts'][arms[0]]['failure_counts'][k]] for k in keys]),'',
'上述是记录的首结果分类，不是唯一因果解释。每项提议的目标空置、原料、能量、候选数/碰撞、表达材料等全部门槛与零项仍在case中；不能由首失败标签断言其余门槛满足。全部死亡、出生、完整阶段物理和身份历史均保留。',
'', '## 同版验证、已知门禁缺口与证据限制', '',
'复核现行1070完整回归PASS（含104专项，77.334秒，wall77.773548秒）、编译和两CLI帮助的已有原始记录、当前执行源码/测试与前后hash。本轮未改科学/控制源码或测试，因此未重复无改动的合成物理suite；真实两CLI及只读审计补充本轮集成证据。本任务没有新科学行为，RED不适用，已有真实RED/GREEN、故障/预算/严格类型/双出生边界测试保留并由原审批绑定，不冒称本轮新跑。', '']
lines +=[table(['当前源码或测试','SHA256'],[[k,h] for k,h in x['current_five_source_hashes'].items()]),'',
'当前完整回归/编译执行入口见[full-revalidated](results/v4-study-047-preflight-joint-validation/full-revalidated/execution.json)、[compile-revalidated](results/v4-study-047-preflight-joint-validation/compile-revalidated/execution.json)；帮助记录只复核当前CLI，所附旧测试快照早于仅测试时标调整，不称为当前测试。历史联合full的2 errors、核验空metadata及当时生产临时失败目录已清理的已知缺口仍照原披露，仅其原trace/日志/源码存在，不改称完整保全。缺POSIX接口模拟不是原生Windows验证。',
'',
'本轮发现的进程门禁问题：生产check_no_other_process与核验check_no_other_process及外层沿用工程wrapper都使用小写python/pypy匹配，未忽略大小写；本机ps实际列为Python。因此这些外层空进程列表和CLI通过本身不能证明在macOS上完备排除其他路线进程。问题属于既有2.1/2.2控制门禁；本轮未补丁源码、改审批或重跑研究。',
'',
'父层在正式根创建、实施者dispatch之前另按两脚本路径直接匹配ps，得到空结果；该检查不依赖解释器大小写，记录原工具chunk与实际过滤stdout，见[父层启动前观察](results/v4-study-047-formal/raw/parent-preflight-observation.json)。它未保存完整全机ps列表和准确观察时钟，不声称对其他-m模块形式完备。实施者运行中曾观察到唯一核验进程PID47257及其wrapper47243；后续大小写不敏感快照保存时两CLI已经结束，结果为空，见[补充快照](results/v4-study-047-formal/raw/process-supplement-during-verifier.json)，其文件名沿创建计划保留，不把事后空表当启动时证明。目录独占、两次唯一调用的顺序记录、源码/来源未变和完整结果一致都保留；是否足以通过正式阶段及最终规格门槛，由新鲜独立审查和父层验收决定。',
'',
'本轮两个实际CLI、完整只读审计及报告数据提取均exit0，没有作者审计失败重试；工程历史审计失败版本仍留在工程归档。本轮没有忽略已知门禁局限来封GO。',
'', '## 逐字节归档与审查入口', '',
f"[归档清单](results/v4-study-047-formal/archive-manifest.json)保留全部{z['original_file_count']}个原文件、{z['original_bytes']}字节的原路径→直接raw副本→tar成员映射。涵盖两路线全部科学/执行文件、201份源码合同快照、运行前brief、wrapper、只读审计与报告数据、父层辅助进程证据和本轮门禁发现。所有成员实际从gzip tar恢复到新临时目录，逐文件比较原件、raw副本和恢复文件的完整bytes/size/SHA256通过；原data不移动、删除或覆盖。",
'',
f"[formal-evidence.tar.gz](results/v4-study-047-formal/formal-evidence.tar.gz)大小{z['archive_bytes']}字节，SHA256 `{z['archive_sha256']}`。每路科学执行存储限单独核算，raw副本、来源快照及压缩归档不混记为单路线科学产物大小。归档执行原始输出另存archive-execution。",
'',
'独立审查入口：本报告、[封口清单](results/v4-study-047-formal/validation-summary.json)、[生产metadata](results/v4-study-047-formal/raw/producer/metadata.json)、[核验metadata](results/v4-study-047-formal/raw/verifier/metadata.json)、[核验proof](results/v4-study-047-formal/raw/verifier/proof.json)、完整原始归档及进程门禁辅助证据。实施者仅写指定正式产物与本报告，不改spec/tasks/LOG、已批准源码/旧文档/审批，不commit或push。',
'', '## 下一研究问题建议（仅规划）', '',
'建议先对保存的全28配对/56arm轨迹做只读方法审查，问题为：双副本窗口出现、延续或终止时，完整组件与成员见证如何对应既有连接、出生、死亡和方向表达事件？以全部无窗口、短窗口、左删失和右删失共同为分母，保留H120003额外短窗、H120011时段迁移及H120015末端右删失，而非只挑最后一例追成功。先区分世界级q区间和成员持续，不把首次合格误作出生，也不把首失败当唯一原因。',
'',
'本轮没有启动Study048、延窗、追加环境票或物理。现有结果只说明人工初态和外部供能下、既定北向前缀之后固定32步中的政策撤除描述，不构成自主生命出现。','']
p=R/'docs/research/v4-study-047-results.zh-CN.md'
with p.open('x') as out:out.write('\n'.join(lines))
print(json.dumps(dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size,status='READY_FOR_REVIEW'),ensure_ascii=False))

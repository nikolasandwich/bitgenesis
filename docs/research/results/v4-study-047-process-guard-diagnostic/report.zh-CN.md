## Debug Report

- ROOT_CAUSE: Producer 的 scripts/run_v4_middle_withdrawal.py:740 与 Verifier 的 scripts/verify_v4_middle_withdrawal.py:841 用不带 IGNORECASE 的小写 python|pypy 正则识别解释器；本机 .venv/bin/python 在 ps 中显示框架可执行文件 basename 为 Python，因此在分析脚本名或 -m 模块之前被当作不相关进程跳过。工程和正式 evidence wrapper 的 process_state 同样以小写 startswith 判断，不能提供独立补偿。现有进程门槛测试仅覆盖小写解释器。
- CATEGORY: LOGIC_ERROR。相同已冻结 Python 3.14.2 运行时、相同命令参数，仅改变 mock ps 中解释器大小写就改变拒绝结果；这不是运行时版本、随机库或依赖不匹配。实际系统名称是触发条件，缺陷在仓库谓词。
- FIX_PLAN:
  1. 回到既有 Producer 2.1 与 Verifier 2.2 的预检所有权，分别仅对解释器 basename 做 .lower() 后执行现有完整正则匹配。保留脚本与模块名的精确大小写、当前 PID 排除、-c/标准输入排除、脚本/-m/解释器参数解析和原失败传播。无需引入依赖、改科学函数、改方法或重拆任务。也可使用显式 ASCII/IGNORECASE，但统一 basename 规范化更小。
  2. 在各自现有测试文件补充固定 ps 字符串反例：python/Python、python3.14/Python3.14、pypy3/PyPy3、实际框架路径；每种覆盖两路线脚本、-m、附着 -m、参数、--。保留自身 PID、无关脚本/模块、python -c 中提及文件名等阴性。先在未修复源上保存新鲜 RED，再在修复源上保存 GREEN；不得调用科学 CLI、生成环境、真实或合成物理 fixture。
  3. 为以后使用的运行前检查修正同类外层匹配；旧工程/正式归档 wrapper 是执行证据，只读保留，不原地修补。不要把同一错误的外层 wrapper 和 CLI 称为两份独立互斥保证。
  4. 由新鲜独立审查重新确认控制面变更、2.1/2.2受影响声明及依赖边界。旧 source、审批 JSON、正式 metadata、raw 执行日志和 commit 必须按原字节保留；新版本审查放新路径，显式区分历史证据的旧 hash 与新实现 hash。不得把旧审批 JSON 的 hash 替换成新源码来伪装旧批准涵盖新版本。
- VERIFICATION:
  - 有效入口是 epoch-3/probe.py，由 epoch-3/record_probe.py 以 .venv/bin/python -B 调用。真实导入两模块，仅直接调用 check_no_other_process，mock 它们的 subprocess.check_output；没有运行 main/run/工程/正式 CLI。
  - 最终 epoch3：74 个 guard 调用，36 个应拒绝的输入放行，全部为大写或实际大写解释器变体；每条路线18个。其余38项按预期拒绝或放行。6个从原 wrapper 精确 AST 提取的 process_state 调用有4个漏检；未执行 wrapper 顶层初始化、运行函数或科学模块。
  - 例：1048258 python scripts/run_v4_middle_withdrawal.py --mode formal 在两条检查函数中均抛 ValueError；仅替换为 Python 后均正常返回。带 -X dev -W error -m scripts.verify_v4_middle_withdrawal 也得到相同大小写差异。原始输入及各次异常详情见 epoch-3/probe-output/results.json。
  - 原始 ps 证明当前非研究诊断进程的解释器 basename 为 Python，sys.executable 是 /Users/todd/Documents/bitgenesis/.venv/bin/python，Python 3.14.2。这个新快照仅验证运行时表现，不是正式运行前的历史快照。
  - epoch3 probe exit=1 是预检需求的预期 RED；原始 stderr 为空，recording wrapper 自身正常完成，0.928009416秒。3894个全部已跟踪文件及28份输入快照前后 SHA256 一致，source/gates/spec/tasks/LOG 无修改。实际科学物理=0、合成物理=0、未来票=0、过去票=0、科学 CLI 调用=0。
  - profile 在导入和所有检查期间拒绝除 guard、require 及编译器声明辅助函数之外的仓库命名函数；random.Random 及 random 模块的抽取、seed、setstate 均设为拒绝。最终 forbidden_calls=[]，记录只含声明辅助函数、check_no_other_process、matches、require。
  - 本轮不重新运行已有同码1070项 suite，不将历史 suite 说成本轮验证。后续修复应运行专门进程门槛用例并独立审查；不要为修复控制面重新运行科学数据。
- NEXT_ACTION: RETRY_TASK
- CONFIDENCE: HIGH
- NOTES:
  - 对本次真实研究证据的影响：本缺陷证明互斥检测存在漏报，不能证明实际发生另一条路线并发、覆盖、重复研究或科学输出损坏。现有 metadata 记录生产 complete、核验 verified，各28配对/1792物理步，执行wrapper exit0，wall分别129.5981286659371秒与159.0859679999994秒，来源commit均为a9efac4e57fd90e70ec3dbc33099b2f2a1272b4f，读源/输出/收尾错误为空。这里只核对这些保存字段及字节，不重新独立评定45份科学输出或代替正式审查。
  - 父层运行前独立文字匹配观察：data/v4-study-047-parent-preflight-observation.json 保存了原tool过滤表达式与stdout。当时正式目录不存在且匹配列表为空，表达式不依赖解释器大小写，因此对本轮实际使用的脚本路径调用有证据价值。但它没有保存完整原始ps、没有精确观察时钟，也未完整覆盖 -m 形式；其显式排除项也保留在原记录。不得补造其时间、完整列表或扩大完备性。
  - 作者“运行期间见到唯一核验进程”的说明，应由正式审查检查对应当时证据；本调查复制的 process-supplement-during-verifier.json 为 matches=[]，不能用文件名推断它是在核验仍运行时取得。结束后的空列表与本次诊断快照都不能倒推启动前全程独占。
  - 可继续：原a9efac4正式结果、两路线原始字节、来源、预算和科学一致性的只读归档及新鲜独立正式审查；可如实说明两条CLI已执行成功。不能无证据宣布此次科学结果无效，也不能把控制面修复当作再跑3584步的理由。
  - 仍须阻断：无条件宣称当前进程防护完备、旧2.1/2.2批准覆盖该新反例、3.1全部门槛已完成、最终规格通过或FEATURE_GO。正式审查须把“保存的科学epoch是否可靠”与“执行互斥证据是否满足完整完成声明”分别列明；未处理的新反例不能由良好科学结果抵消。本调试者不给APPROVED。
  - 来源保全与后续修复：现在先冻结旧epoch，再做最小控制面修复及新鲜独立审查。scripts/middle_withdrawal_inputs.py:261–293要求当前文件等于审批绑定；修复后旧hash门槛理应失效，不能关闭检查。历史正式结果始终绑定a9efac4及归档源码；新审查可通过明确的历史归档映射核对旧证据，并比较新旧差异只在进程检查/对应测试。是否恢复当前阶段完整完成声明由独立审查与父层完成核验决定，不能伪造以新代码运行过旧结果。此处理在现有2.1/2.2边界内可修，不需仅因任务规划存在问题而询问用户。
  - 本轮三个诊断epoch均保留。初版profile误拒绝Python3.14惰性注解__annotate__，异常被类型声明内部处理并导致profile停止，故不采用其非科学调用计数作最终保证；epoch2在固定METRICS字符串生成式拒绝并终止，保留原traceback/stderr/exit；epoch3只扩大编译器声明辅助函数白名单后得到完整隔离证据。准备阶段缺失steering/错误候选wrapper路径、apply_patch后置hook缺失和独占备用写入FileExistsError均见preparation-errors.json，没有覆盖失败或源文件。
  - 仓库当前diff为空；git status中的formal归档与results中文报告为author同时新增，未纳入本调试写入或进行编辑。诊断独占新增范围仅本目录，无commit/spec/tasks/LOG修改。

官方技术依据：Python文档的 fullmatch 默认 flags=0，忽略大小写需显式提供 IGNORECASE；这与本机机械反例一致。[Python 3.14 re 文档](https://docs.python.org/3.14/library/re.html#re.IGNORECASE)。文档只是支持匹配语义；分类核心证据为实际模块与当前运行时的反例。

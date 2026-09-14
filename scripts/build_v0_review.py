"""Build a local Chinese review page from completed campaign artifacts."""

import argparse
from collections import defaultdict
from html import escape
import json
import os
from pathlib import Path
from statistics import mean
from urllib.parse import quote


def require_run_grid(records, treatments, seeds):
    keys = [(row["treatment"], row["seed"]) for row in records]
    expected = {(treatment, seed) for treatment in treatments for seed in seeds}
    if len(keys) != len(expected) or set(keys) != expected:
        raise ValueError("Review requires a complete, unique treatment/seed grid")


def require_followup_records(records, reference, verified):
    def key(row):
        return (row["movement_cost"], row["initial_b"], row["treatment"], row["seed"])
    selected = {key(r) for r in reference if r["treatment"] == "neutral" and r["a"] > 0 and r["b"] > 0}
    indexed = {key(r): r for r in records}
    audited = {key(r): r for r in verified}
    if len(records) != 4 or len(verified) != 4 or len(selected) != 4 or set(indexed) != selected or indexed != audited:
        raise ValueError("Review requires the complete verified conditional follow-up cohort")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--campaigns", type=int, choices=(8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21), default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    args.output = args.output or args.data_root / f"review-v0-{args.campaigns}.html"
    campaigns = [json.loads((args.data_root / f"campaign-{i:03d}" / "results.json").read_text(encoding="utf-8"))
                 for i in range(1, args.campaigns + 1)]
    inventory_path = Path(__file__).resolve().parents[1] / "experiments/v0/campaign-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))["campaigns"][:args.campaigns]
    if [entry["id"] for entry in inventory] != [f"{i:03d}" for i in range(1, args.campaigns + 1)]:
        raise ValueError("Review scope differs from campaign inventory")
    if [len(c) for c in campaigns] != [entry["executions"] for entry in inventory]:
        raise ValueError("Expected complete campaign counts")
    if any(row["tick"] != entry["ticks_per_execution"] for rows, entry in zip(campaigns, inventory) for row in rows):
        raise ValueError("Review horizons differ from campaign inventory")
    for i in range(2, args.campaigns + 1):
        metadata = json.loads((args.data_root / f"campaign-{i:03d}" / "metadata.json").read_text(encoding="utf-8"))
        if metadata["status"] != "complete":
            raise ValueError(f"Campaign {i} is not marked complete")
    if not (args.data_root / "acceptance-v0" / "lineage.html").exists():
        raise ValueError("Generate the acceptance-v0 demonstration before building the review")
    def link(path):
        return quote(os.path.relpath(path, args.output.parent).replace("\\", "/"), safe="/.-")
    def table(headers, rows):
        return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{escape(str(h))}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join(f'<td>{escape(str(c))}</td>' for c in row)+'</tr>' for row in rows) + '</tbody></table></div>'
    groups = defaultdict(list)
    for row in campaigns[1]:
        groups[(row["movement_cost"], row["trait"])].append(row)
    trait_rows = [[cost, f"{trait/10:g}%", f"{mean(r['late_mean_population'] for r in rows):.2f}",
                   f"{sum(r['extinction_tick'] is not None for r in rows)}/{len(rows)}"]
                  for (cost, trait), rows in sorted(groups.items())]
    groups = defaultdict(list)
    for row in campaigns[2]:
        groups[(row["movement_cost"], row["initial_b"], row["treatment"])].append(row)
    competition_rows = []
    for (cost, initial, treatment), rows in sorted(groups.items()):
        competition_rows.append([cost, f"{initial/80:.0%}", "高移动 vs 低移动" if treatment == "competition" else "相同策略、中性标签",
                                 sum(r["b"] > 0 and r["a"] == 0 for r in rows),
                                 sum(r["a"] > 0 and r["b"] == 0 for r in rows),
                                 sum(r["a"] > 0 and r["b"] > 0 for r in rows),
                                 sum(r["population"] == 0 for r in rows)])
    runs = sum(len(c) for c in campaigns)
    ticks = sum(r["tick"] for c in campaigns for r in c)
    replay = link(args.data_root / "acceptance-v0" / "index.html")
    lineage = link(args.data_root / "acceptance-v0" / "lineage.html")
    table_traits = table(["移动成本", "每步移动概率", "后期平均种群", "灭绝次数"], trait_rows)
    table_competition = table(["移动成本", "B 初始比例", "实验", "仅 B 存活", "仅 A 存活", "两组存活", "整体灭绝"], competition_rows)
    regimes = defaultdict(list)
    for row in campaigns[3]:
        regimes[row["regrowth_probability"]].append(row)
    def span(rows, key):
        low, high = min(r[key] for r in rows), max(r[key] for r in rows)
        return str(low) if low == high else f"{low}–{high}"
    table_regimes = table(["每格每步再生概率", "终点种群", "后 1,000 步出生数", "存续创始谱系", "灭绝次数"],
                         [[f"{p/10:g}%", span(rows, "population"), span(rows, "late_births"),
                           span(rows, "founder_lineages"), f"{sum(r['extinction_tick'] is not None for r in rows)}/5"]
                          for p, rows in sorted(regimes.items())])
    sizes = defaultdict(list)
    for row in campaigns[4]:
        sizes[(row["width"], row["treatment"])].append(row)
    table_sizes = table(["世界大小", "条件", "初始谱系", "终点谱系", "到达单一谱系"],
                       [[f"{width}×{width}", "可变性状＋突变" if treatment == "evolving" else "相同性状、中性标签",
                         rows[0]["initial_population"], span(rows, "founder_lineages"),
                         f"{sum(r['first_single_founder_tick'] is not None for r in rows)}/5"]
                        for (width, treatment), rows in sorted(sizes.items())])
    lineage_figure = link(args.data_root.parent / "docs/research/figures/campaign-005-lineages.png")
    extinction_figure = link(args.data_root.parent / "docs/research/figures/campaign-006-extinction.png")
    extinction_groups = defaultdict(list)
    for row in campaigns[5]:
        extinction_groups[row["regrowth_probability"]].append(row)
    extinction_rows = []
    for probability, rows in sorted(extinction_groups.items()):
        deaths = [r["extinction_tick"] for r in rows if r["extinction_tick"] is not None]
        extinction_rows.append([f"{probability}/1000", f"{len(deaths)}/{len(rows)}",
                                f"{min(deaths)}–{max(deaths)}" if deaths else "未观察到灭绝",
                                span(rows, "population"), f"{mean(r['late_mean_population'] for r in rows):.2f}"])
    table_extinction = table(["再生概率", "灭绝次数", "仅灭绝运行的时间范围", "终点种群", "后期平均种群"], extinction_rows)
    establishment = defaultdict(list)
    for row in campaigns[6]:
        establishment[(row["founder_trait"], row["mutation_probability"])].append(row)
    table_establishment = table(["初始性状", "每次出生突变尝试", "活到 500 步", "活到 5,000 步"],
        [["随机" if trait == "random" else trait, f"{mutation/10:g}%",
          f"{sum(r['population_at_500'] > 0 for r in rows)}/{len(rows)}",
          f"{sum(r['population'] > 0 for r in rows)}/{len(rows)}"]
         for (trait, mutation), rows in sorted(establishment.items())])
    initial_food = defaultdict(list)
    for row in campaigns[7]:
        initial_food[row["initial_food"]].append(row)
    table_initial_food = table(["每格初始食物", "活到 500 步", "活到 5,000 步", "活到 10,000 步"],
        [[food, f"{sum(r['population_at_500'] > 0 for r in rows)}/{len(rows)}",
          f"{sum(r['population_at_5000'] > 0 for r in rows)}/{len(rows)}",
          f"{sum(r['population'] > 0 for r in rows)}/{len(rows)}"] for food, rows in sorted(initial_food.items())])
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BitGenesis · V0 研究验收</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f4f2e9;color:#263b34;font:16px system-ui,"Microsoft YaHei",sans-serif}}main{{max-width:1120px;margin:auto;padding:48px 26px 80px}}.eyebrow{{font-size:12px;letter-spacing:3px;color:#557364}}h1{{font-size:48px;line-height:1.2;letter-spacing:-2px;margin:14px 0 20px}}h2{{font-size:26px;line-height:1.3;margin:0 0 18px}}h3{{font-size:17px}}p{{line-height:1.8;max-width:920px;color:#50665c}}.lead{{font-size:19px}}.rule{{font-family:monospace;font-size:18px;color:#557364}}.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:30px 0}}.stat{{background:#e5ebdf;border-radius:12px;padding:22px}}.stat b{{font-size:36px;display:block;font-weight:600}}.stat span{{font-size:13px;color:#597060}}.actions{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0 38px}}.button{{padding:14px 20px;border-radius:7px;background:#2d5948;color:white;text-decoration:none;font-weight:600}}.button.secondary{{background:transparent;color:#2d5948;border:1px solid #789383}}section{{padding:32px 0;border-top:1px solid #ced8cb}}.badge{{display:inline-block;font-size:12px;background:#dbe8d6;color:#346242;border-radius:20px;padding:5px 10px}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:26px}}.card{{padding:22px;background:#fffef8;border:1px solid #d8dfd1;border-radius:12px}}.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px;margin:15px 0 25px}}th,td{{text-align:left;padding:12px 10px;border-bottom:1px solid #d8dfd1;white-space:nowrap}}th{{color:#5c7566;font-size:12px}}.small{{font-size:13px}}a{{color:#25634d}}code{{background:#e5ebdf;padding:2px 5px;border-radius:3px}}@media(max-width:700px){{h1{{font-size:35px}}.stats,.columns{{grid-template-columns:1fr}}main{{padding:30px 18px}}.stat b{{font-size:28px}}}}
</style><main><div class="eyebrow">BITGENESIS / RESEARCH NOTEBOOK / V0</div><h1>先造世界，再观察生命。</h1>
<div class="rule">Simple Rules + Energy + Information + Time → ?</div>
<p class="lead">最小达尔文世界已经运行。个体会进食、消耗能量、复制、突变和死亡；研究开始从“它动起来了”转向“为什么是这种行为留下了后代”。</p>
<div class="stats"><div class="stat"><b>{runs}</b><span>已完成的受控实验</span></div><div class="stat"><b>{ticks:,}</b><span>累计实验时间步，每步检查能量和空间约束</span></div><div class="stat"><b>V0</b><span>当前唯一运行阶段；后续阶段仍为研究路线图</span></div></div>
<div class="actions"><a class="button" href="{replay}">打开世界回放 →</a><a class="button secondary" href="{lineage}">追踪个体谱系 →</a><a class="button secondary" href="https://github.com/nikolasandwich/bitgenesis">查看 GitHub 仓库 ↗</a></div>
<section><span class="badge">先看这三点</span><div class="columns"><div><h3>繁殖成功不等于种群最大</h3><p>低成本时，高移动类型能在竞争中取代低移动类型；但单独运行的低移动种群，能维持更多个体。没有人为给“种群数量”打分。</p><h3>优势取决于世界规则</h3><p>提高移动成本后，竞争结果通常反转。这里出现的是特定环境中的选择，不是通用智能。</p></div><div><h3>持续繁殖不等于开放式进化</h3><p>第一轮十个长跑实验最后都只剩一个创始谱系。突变仍会产生差异，但还没有持续形成丰富的新功能或生态。</p><p class="small">个体、基因含义、繁殖方式和能量规则都是明确设计的。未实现食物感知、记忆、神经控制器或复杂生物学。</p></div></div></section>
<section><h2>01 / 一个可复核的世界</h2><div class="columns"><div class="card"><h3>回放里看什么</h3><p>拖动时间轴，观察食物与个体分布。切换基因和创始谱系着色，查看种群、移动概率和谱系数量随时间变化。</p></div><div class="card"><h3>谱系里查什么</h3><p>示例运行可查个体 <code>1640</code>：它的父代是 <code>1618</code>，创始祖先是 <code>24</code>。点击祖先按钮查看每一代的出生、死亡、遗传值和直接子代。</p></div></div><p class="small">演示是种子 42、1,000 步的独立运行。每个实验目录同时保存配置、代码来源、逐步指标和原始记录；验收页来自已完成的实验结果，不会修改模拟状态。</p></section>
<section><h2>02 / 固定策略，比较生存</h2><p>每种条件用十个独立种子运行 2,000 步，关闭突变。表中后期种群为最后 500 步均值，灭绝后的零值也计入。</p>{table_traits}<p class="small">完全不移动的种群在这些条件下全部灭绝；移动越频繁，并不意味着能维持越多个体。</p></section>
<section><h2>03 / 让策略直接竞争</h2><p>A 为 25% 移动，B 为 100% 移动；中性对照中两组都为 25%，标签本身没有作用。每行十个种子，每次 3,000 步。“两组存活”只是终点状态，不表示永久共存。</p>{table_competition}<p class="small">整体灭绝与某一谱系胜出分开记录。样本支持初步比较，不能把十次实验的频率当成精确概率。</p></section>
<section><h2>04 / 活着，也可能停止演化</h2><p>每种资源条件运行五个种子、10,000 步。极充足条件下，世界在第 22–24 步就被填满，之后没有新的出生和死亡，个体仅继续积累能量。</p>{table_regimes}<p class="small">80 个创始谱系全部保留，并不表示创新更丰富：它们都没有死亡。这是当前“无衰老、无能量储存上限、繁殖需要空位”规则的边界情况，保留为反例。</p></section>
<section><h2>05 / 世界大小会改变观察结果</h2><p>保持初始密度不变，每种条件五个种子、10,000 步。大世界保留更多祖先标签，但保留比例并不更高。相同行为的中性标签也会消失，单一谱系胜出不等于策略优越。</p>{table_sizes}<img src="{lineage_figure}" alt="不同世界规模下五个种子的创始谱系数量随时间变化；粗线是中位数，不是置信区间。" style="width:100%;height:auto"><p class="small">这些是有限时长的祖先数量，不是物种数量或开放式创新。完整报告解释了种群规模和行为差异之间的混杂因素。</p></section>
<section><h2>06 / 暂时活着，不等于稳定生存</h2><p>五种稀缺资源条件，各十个种子、5,000 步。10/1000 的条件全部灭绝，但有两次坚持超过 1,000 步；15/1000 则出现早期灭绝与持续到观察终点并存。</p>{table_extinction}<img src="{extinction_figure}" alt="五种资源条件下尚未灭绝的运行比例，以及包含灭绝零值的各个种子后期种群。" style="width:100%;height:auto"><p class="small">后期平均种群包含所有种子和灭绝后的零值。活到 5,000 步的运行，其最终寿命仍未知。20、30、40 三组存活曲线重合；本实验没有证明永久稳定或确定普适资源阈值。</p></section>
<section><h2>07 / 存活不必依赖新变异</h2><p>稀缺资源条件下，各十个种子比较初始性状与有无突变。250、1000 分别表示 25%、100% 的随机移动概率。初始性状完全相同、关闭突变的种群，也有存活到 5,000 步的案例。</p>{table_establishment}<p class="small">开启突变后，初始固定性状仍可能改变。关闭突变的随机初始组仍有可选择的遗传差异。组间小样本频率差不能证明普遍的突变利弊，有限时存活也不等于新适应。</p></section>
<section><h2>08 / 开局资源帮助建立，却不保证维持</h2><p>固定性状 250、关闭突变，保持持续食物再生不变。每种初始食物条件十个种子、10,000 步。没有初始食物的种群全部在第 30–65 步灭绝；有初始食物的种群全部建立，但随后仍有不少灭绝。</p>{table_initial_food}<p class="small">空食物开局仍有能量为 24 的创始个体；这不是无资源或生命起源实验。终点存活者的后续寿命仍未知。</p></section>
<section><h2>复核与恢复</h2><p>完整演示支持独立核对指标、事件和谱系。后续指标实验分别复算了其声明的观测量与能量收支。断点工具可精确继续世界状态，旧回放和指标文件不会被续写。</p><p class="small">核验检查记录是否一致，不证明生物学真实性。当前核心仍未实现食物感知、记忆或神经控制器。</p></section>
<section><h2>接下来如何继续</h2><p>保持 V0 规则与旧实验可重放，区分稀缺资源下的早期建立过程和后续适应，再决定是否进入可进化控制器阶段。先增加证据，再增加生物复杂度。</p><p class="small">详细协议与报告位于仓库的 <code>experiments/v0/</code>、<code>docs/research/</code>；当前验收检查点见 <code>ACCEPTANCE.md</code>。本页为本地静态研究快照。</p></section></main></html>'''
    if args.campaigns >= 9:
        require_run_grid(campaigns[8], ("low", "food", "stored"), range(800, 810))
        allocations = defaultdict(list)
        for row in campaigns[8]:
            allocations[row["treatment"]].append(row)
        labels = {"low": "低能量基线", "food": "环境食物", "stored": "体内储能"}
        allocation_table = table(["条件", "初始总能量", "活到 500 步", "活到 5,000 步", "活到 10,000 步"],
            [[labels[name], 1920 if name == "low" else 7040,
              f"{sum(r['population_at_500'] > 0 for r in allocations[name])}/10",
              f"{sum(r['population_at_5000'] > 0 for r in allocations[name])}/10",
              f"{sum(r['population'] > 0 for r in allocations[name])}/10"] for name in ("low", "food", "stored")])
        allocation_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-009-early.png")
        allocation_section = f'''<section><h2>09 / 总能量相同，分配方式也重要</h2><p>两个主要组的初始总能量同为 7040，分别放在环境食物中或个体体内；低能量基线为 1920。每组十个新种子、10,000 步，持续资源再生参数相同。</p>{allocation_table}<img src="{allocation_figure}" alt="三十个世界前一百步的种群轨迹；体内储能组先快速繁殖，再灭绝。各图使用相同坐标。" style="width:100%;height:auto"><p class="small">图中细线为全部种子，粗线为组平均。早期窗口是事后分析。体内储能组灭绝时世界仍有食物，但这些总量不能说明个体当时是否能获取食物，也没有单独证明繁殖高峰导致灭绝。初始总量相同不保证后续实际输入相同。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', allocation_section + '<section><h2>复核与恢复</h2>')
    if args.campaigns >= 10:
        treatments = ("food-40", "stored-40", "food-160", "stored-160")
        require_run_grid(campaigns[9], treatments, range(900, 910))
        thresholds = defaultdict(list)
        for row in campaigns[9]:
            thresholds[row["treatment"]].append(row)
        threshold_table = table(["能量分配", "繁殖阈值", "活到 500 步", "活到 10,000 步", "前 100 步平均出生数"],
            [["环境食物" if name.startswith("food") else "体内储能", name.split("-")[1],
              f"{sum(r['population_at_500'] > 0 for r in thresholds[name])}/10",
              f"{sum(r['population'] > 0 for r in thresholds[name])}/10",
              f"{mean(r['births_at_100'] for r in thresholds[name]):.1f}"] for name in treatments])
        threshold_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-010-survival.png")
        threshold_section = f'''<section><h2>10 / 繁殖阈值会改变存活结果</h2><p>初始总能量相同，交叉比较能量分配与繁殖阈值。每组十个新种子、10,000 步。提高阈值后，两种分配的终点存活均增加，但这来自人为参数干预，没有进化出新的繁殖策略。</p>{threshold_table}<img src="{threshold_figure}" alt="四组完整观察期与早期放大的存活比例曲线；终点存活者的后续寿命未知。" style="width:100%;height:auto"><p class="small">较高阈值下的 17 个终点存活世界，在最后 1,000 步都仍有出生和死亡。阈值会共同影响繁殖时间、能量分配和竞争，不能据此认定单一机制或普适最优阈值。每条曲线保留全部十次运行，右图是同一数据的放大。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', threshold_section + '<section><h2>复核与恢复</h2>')
    if args.campaigns >= 11:
        require_run_grid(campaigns[10], ("food-160", "stored-160"), range(900, 910))
        long_groups = defaultdict(list)
        for row in campaigns[10]:
            long_groups[row["treatment"]].append(row)
        long_table = table(["原队列", "活到 10,000 步", "活到 50,000 步", "活到 100,000 步"],
            [["环境食物" if name == "food-160" else "体内储能",
              f"{sum(r['population_at_10000'] > 0 for r in rows)}/10",
              f"{sum(r['population_at_50000'] > 0 for r in rows)}/10",
              f"{sum(r['population'] > 0 for r in rows)}/10"] for name, rows in sorted(long_groups.items())])
        long_section = f'''<section><h2>11 / 同一批世界，观察得更久</h2><p>复查第十轮两组较高阈值的全部 20 个世界，包括原先早期灭绝的三个种子。逐步核对前 10,000 步后，延长到 100,000 步。原先 17 个存活世界均维持到新终点。</p>{long_table}<p class="small">这是同一队列的纵向观察，不增加独立种子样本。20 次执行包含 200 万个计算步，其中 20 万步重放原前缀、180 万步增加观察时长。终点存活仍不证明永久稳定；长期存活世界最终都只有一个创始谱系，且没有新移动性状产生。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', long_section + '<section><h2>复核与恢复</h2>')
        replayed = sum(entry["executions"] * entry["replayed_prefix_ticks_per_execution"] for entry in inventory)
        followups = sum(entry["executions"] for entry in inventory if entry["followup_of"] is not None)
        page = page.replace("已完成的受控实验", "已完成的执行（含延长复查）")
        workload_note = f'<p class="small">工作量统计包含 {followups} 次既有队列复查和 {replayed:,} 步前缀重放。执行次数不等于独立样本数。</p>'
        page = page.replace('<div class="actions">', workload_note + '<div class="actions">', 1)
    if args.campaigns >= 12:
        treatments = tuple(f"{a}-{t}-cost-{c}" for a in ("food", "stored") for t in (40, 160) for c in (0, 4))
        require_run_grid(campaigns[11], treatments, range(1000, 1010))
        cost_groups = defaultdict(list)
        for row in campaigns[11]:
            cost_groups[row["treatment"]].append(row)
        cost_rows = []
        for treatment in treatments:
            allocation, threshold, _, cost = treatment.split("-")
            rows = cost_groups[treatment]
            cost_rows.append(["环境食物" if allocation == "food" else "体内储能", threshold, cost,
                              f"{sum(r['population_at_500'] > 0 for r in rows)}/10",
                              f"{sum(r['population'] > 0 for r in rows)}/10",
                              f"{mean(r['births_at_100'] for r in rows):.1f}"])
        cost_table = table(["能量分配", "繁殖阈值", "直接出生扣费", "活到 500 步", "活到 10,000 步", "前 100 步平均出生数"], cost_rows)
        cost_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-012-survival.png")
        cost_section = f'''<section><h2>12 / 免除出生扣费，仍可能早期灭绝</h2><p>在两种能量分配下，交叉比较繁殖阈值 40/160 与直接出生扣费 0/4。每组十个新种子、10,000 步，移动性状固定且没有突变。</p>{cost_table}<img src="{cost_figure}" alt="八组存活曲线，按能量分配分行；右列放大前五百步。高阈值的两种扣费曲线重合。" style="width:100%;height:auto"><p>体内储能、低阈值组在零扣费下仍十次全部早期灭绝，说明正的直接出生扣费不是这些失败的必要条件。零扣费仍会分割亲代能量、增加消费者并占据空间，不能据此确定唯一致死机制。</p><p class="small">高阈值的存活曲线重合，不等于内部过程相同。事后开局能量账显示：储能低阈值组免除平均 864.8 单位出生扣费后，基础生存与移动支出合计增加 885.6 单位；这是动态账目，不是单一路径的因果估计。全部种子和灭绝均保留。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', cost_section + '<section><h2>复核与恢复</h2>')
    if args.campaigns >= 13:
        require_run_grid(campaigns[12], ("mutation", "no-mutation"), range(1100, 1105))
        coverage_rows = [["有突变" if r["treatment"] == "mutation" else "无突变", r["seed"],
                          r["initial_genome_values"], r["ever_genome_values"],
                          r["new_values_last_10000"], r["genome_variants"]]
                         for r in sorted(campaigns[12], key=lambda r: (r["treatment"], r["seed"]))]
        coverage_table = table(["处理", "种子", "初始取值数", "累计取值数", "末一万步新增", "终点活体取值数"], coverage_rows)
        coverage_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-013-coverage.png")
        coverage_section = f'''<section><h2>13 / 更多基因取值，不等于新的功能</h2><p>有突变与无突变各五个新种子，每个世界观察 50,000 步，并记录所有出生个体的基因。累计取值从出生表独立重建；全部十个世界活到终点，且最终都只剩一个创始谱系。</p>{coverage_table}<img src="{coverage_figure}" alt="累计基因取值与活体基因取值对照；左图保留累计变化点，右图每百步采样，纵轴范围不同。" style="width:100%;height:auto"><p>有突变组末一万步新增 0–22 个取值，四个世界仍出现新数值；这既不能证明永远创新，也不能证明已经永久停滞。无突变组始终局限于初始取值。</p><p class="small">V0 的基因仍只编码 1001 种移动概率。更长谱系和新的数值不会自动增加感觉、记忆或行动种类；这个限制针对遗传控制方式，不是说整个世界只有 1001 种状态。图中两面板纵轴不同，活体曲线可能省略短暂波动。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', coverage_section + '<section><h2>复核与恢复</h2>')
    if args.campaigns >= 14:
        records = campaigns[13]
        keys = [(r["movement_cost"], r["initial_b"], r["treatment"], r["seed"]) for r in records]
        expected = {(c, b, t, seed) for c in (1, 2, 3, 4) for b in (8, 72)
                    for t in ("competition", "neutral") for seed in range(1200, 1210)}
        if len(keys) != 160 or set(keys) != expected:
            raise ValueError("Review requires complete frequency-cost seed grid")
        frequency_rows = []
        for cost in (1, 2, 3, 4):
            for initial_b in (8, 72):
                for treatment in ("competition", "neutral"):
                    selected = [r for r in records if (r["movement_cost"], r["initial_b"], r["treatment"])
                                == (cost, initial_b, treatment)]
                    frequency_rows.append([cost, f"{initial_b}/80", "不同移动性状" if treatment == "competition" else "相同性状标签",
                        sum(r["a"] > 0 and r["b"] == 0 for r in selected),
                        sum(r["b"] > 0 and r["a"] == 0 for r in selected),
                        sum(r["a"] > 0 and r["b"] > 0 for r in selected),
                        sum(r["population"] == 0 for r in selected)])
        frequency_table = table(["移动成本", "初始 B", "条件", "仅 A 存活", "仅 B 存活", "两组仍在", "整体灭绝"], frequency_rows)
        frequency_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-014-outcomes.png")
        frequency_section = f'''<section><h2>14 / 初始多数，也可能一起灭绝</h2><p>四档移动成本、两种初始比例，每种条件十个新种子，观察 3,000 步。不同性状组中 A 为 25% 移动、B 为 100%；中性标签对照中两者均为 25%，所有条件关闭突变。</p>{frequency_table}<img src="{frequency_figure}" alt="第十四轮全部一百六十个世界的逐种子结果；A、B 表示单独存活，AB 表示两组仍在，X 表示整体灭绝。" style="width:100%;height:auto"><p>成本 1、2 时，两种比例的竞争组都由 B 单独存活到终点；成本 4 且 B 起初占 90% 时，十个世界中五个整体灭绝。不能只看幸存者来比较胜负。</p><p class="small">图中每格是一个世界，六个灭绝案例和四个中性对照的双群体终点全部保留。起初占多数不是持续存活的保证；终点两组仍在不证明稳定共存。这些是从开局共同建立的群体，尚未检验向稳定居民种群引入稀有类型的结果。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', frequency_section + '<section><h2>复核与恢复</h2>')
    if args.campaigns >= 15:
        verified_path = Path(__file__).resolve().parents[1] / "docs/research/results/campaign-015-verification.json"
        verified = json.loads(verified_path.read_text(encoding="utf-8"))
        records = campaigns[14]
        require_followup_records(records, campaigns[13], verified["runs"])
        followup_rows = []
        for r in sorted(records, key=lambda r: (r["movement_cost"], r["initial_b"], r["seed"])):
            loss = f"A / {r['a_loss_tick']:,}" if r["a_loss_tick"] is not None else f"B / {r['b_loss_tick']:,}"
            start = r["observations"]["3000"]
            followup_rows.append([r["movement_cost"], f"{r['initial_b']}/80", r["seed"],
                                  f"{start['a']} / {start['b']}", loss, f"{r['a']} / {r['b']}"])
        followup_table = table(["移动成本", "初始 B", "种子", "3,000 步 A / B", "消失组 / 时间步", "30,000 步 A / B"], followup_rows)
        followup_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-015-followup.png")
        followup_section = f'''<section><h2>15 / 暂时两组都在，后来只剩一组</h2><p>把第十四轮终点仍有两组中性标签的全部四个世界延长观察到 30,000 步。两组移动性状相同，突变关闭；四个案例均在第 3,625—4,765 步失去一组，剩余组维持到新终点。</p>{followup_table}<img src="{followup_figure}" alt="四个条件选择世界的 B 标签比例：左列显示前六千步细节，右列显示完整三万步；灰区是原三千步观察窗，圆点标记标签消失。" style="width:100%;height:auto"><p>原来的双组终点没有持续下去，因此不能把它当作稳定共存的证据。0% 或 100% 的水平线只表示一个标签存活，不表示种群停止出生、死亡或数量变化。</p><p class="small">这是按既有终点选择的四个案例，不是新增独立种子；同一数值种子 1208 出现在两个不同条件。12,000 步重放原前缀，108,000 步增加观察时长。不能据此估计普遍共存率或证明所有世界最终必然只剩一组。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>', followup_section + '<section><h2>复核与恢复</h2>')
    if args.campaigns >= 16:
        records = campaigns[15]
        require_run_grid([{"treatment":r["arm"],"seed":r["seed"]} for r in records],
                         ("uniform","dispersed","block"), range(1300,1310))
        verified_path = Path(__file__).resolve().parents[1] / "docs/research/results/campaign-016-verification.json"
        verified = json.loads(verified_path.read_text(encoding="utf-8"))
        if ({(r["arm"],r["seed"]):r for r in records}
                != {(r["arm"],r["seed"]):r for r in verified["runs"]}):
            raise ValueError("Food geometry records differ from independent verification")
        geometry_rows = []
        for arm,label in (("uniform","均匀铺开"),("dispersed","随机散布"),("block","集中成片")):
            selected = [r for r in records if r["arm"] == arm]
            deaths = [r["extinction_tick"] for r in selected if r["extinction_tick"] is not None]
            geometry_rows.append([label,f"{sum(r['population_at_500']>0 for r in selected)}/10",
                f"{sum(r['population_at_5000']>0 for r in selected)}/10",
                f"{sum(r['population']>0 for r in selected)}/10",
                f"{min(deaths):,}–{max(deaths):,}" if deaths else "没有观察到灭绝"])
        geometry_table = table(["初始食物分布","活到 500 步","活到 5,000 步","活到 10,000 步","已灭绝世界的时间范围"],geometry_rows)
        geometry_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-016-geometry.png")
        geometry_section = f'''<section><h2>16 / 食物总量相同，分布也会改变过程</h2><p>三组都从 5,120 食物能量与 1,920 个体能量开始，固定移动性状 250、关闭突变。每个种子的三组共享创始个体与初始世界随机状态，仅在开局放置不同食物地图，之后使用相同 V0 规则。</p>{geometry_table}<img src="{geometry_figure}" alt="上方是种子 1300 的三种初始食物地图，红圈表示相同创始个体；下方以对数时间轴展示全部三十个世界的灭绝时间。" style="width:100%;height:auto"><p>一万步时三组都已灭绝，但集中成片组在第 110–169 步就全部消失；只看最终结果会漏掉建立阶段和存活时长的差异。</p><p class="small">随机散布与集中成片共享相同食物取值集合，只改变位置。均匀组还改变了每格食物量，不能作为单纯的位置对照。上方地图只展示第一个预定种子，下方保留全部十组配对；初始随机状态相同不保证之后随机调用相同。这些有限种子结果不能证明食物集中总是有害，更没有检验感知能力。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>',geometry_section+'<section><h2>复核与恢复</h2>')
    if args.campaigns >= 17:
        records = campaigns[16]
        treatments = tuple(f"{a}-{t}" for a in ("dispersed","block") for t in (40,160))
        require_run_grid([{**r,"treatment":f"{r['arm']}-{r['birth_threshold']}"} for r in records], treatments, range(1400,1410))
        verified_path = Path(__file__).resolve().parents[1] / "docs/research/results/campaign-017-verification.json"
        verified = json.loads(verified_path.read_text(encoding="utf-8"))
        key = lambda r: (r["arm"],r["birth_threshold"],r["seed"])
        if len(verified["runs"]) != 40 or {key(r):r for r in records} != {key(r):r for r in verified["runs"]}:
            raise ValueError("Geometry-threshold records differ from independent verification")
        threshold_rows = []
        for arm,label in (("dispersed","随机散布"),("block","集中成片")):
            for threshold in (40,160):
                selected = [r for r in records if r["arm"]==arm and r["birth_threshold"]==threshold]
                births = [r["births_at_100"] for r in selected]
                threshold_rows.append([label,threshold,f"{sum(r['population_at_500']>0 for r in selected)}/10",
                    f"{sum(r['population_at_5000']>0 for r in selected)}/10",
                    f"{sum(r['population']>0 for r in selected)}/10",f"{min(births)}–{max(births)}"])
        threshold_table = table(["食物布局","繁殖阈值","活到 500 步","活到 5,000 步","活到 10,000 步","前百步出生数范围"],threshold_rows)
        threshold_figure = link(Path(__file__).resolve().parents[1] / "docs/research/figures/campaign-017-threshold.png")
        threshold_section = f'''<section><h2>17 / 改变繁殖条件，改变存活结果</h2><p>用十个新种子交叉比较两种布局与繁殖阈值 40/160，共四十个世界。各组都观察 10,000 步；早期指标和观察窗口在运行前固定。</p>{threshold_table}<img src="{threshold_figure}" alt="全部四十个世界：上方圆点为实际灭绝时间，三角形为万步时仍存活；下方为前百步出生数，细线连接同一种子的两档阈值。" style="width:100%;height:auto"><p>较高阈值下二十个世界全部存活到万步，原阈值下只有两个。较高阈值也压低早期繁殖高峰，但它同时改变个体储能、种群数量和之后的互动，不能只归因于拥挤或某一种能量开销。</p><p class="small">上图三角形不是在万步灭绝；下图连线不是时间轨迹。四十次执行对应十组配对种子，初始个体与随机状态相同不保证后续随机调用相同。新种子下原阈值食物块组有世界活到 3,903 步，说明第十六轮的灭绝范围不能推广为普遍上限。仍没有感知、记忆或永久稳定的证据。</p></section>'''
        page = page.replace('<section><h2>复核与恢复</h2>',threshold_section+'<section><h2>复核与恢复</h2>')
    if args.campaigns >= 18:
        records=campaigns[17]
        treatments=[f'{a}-{t}-{c}' for a in ('dispersed','block') for t in (40,160) for c in (0,1)]
        require_run_grid([{**r,'treatment':f"{r['arm']}-{r['birth_threshold']}-{r['movement_cost']}"} for r in records],treatments,range(1500,1510))
        root=Path(__file__).resolve().parents[1]
        verification=json.loads((root/'docs/research/results/campaign-018-verification.json').read_text(encoding='utf-8'))
        key=lambda r:(r['arm'],r['birth_threshold'],r['movement_cost'],r['seed'])
        if sorted(records,key=key)!=sorted(verification['runs'],key=key):
            raise ValueError('Movement-charge records differ from independent verification')
        charge_rows=[]
        for arm,label in (('dispersed','分散'),('block','成片')):
            for threshold in (40,160):
                for cost in (0,1):
                    selected=[r for r in records if (r['arm'],r['birth_threshold'],r['movement_cost'])==(arm,threshold,cost)]
                    charge_rows.append([label,threshold,cost,
                        f"{sum(r['population_at_500']>0 for r in selected)}/10",
                        f"{sum(r['population_at_5000']>0 for r in selected)}/10",
                        f"{sum(r['population']>0 for r in selected)}/10"])
        charge_table=table(['食物布局','繁殖阈值','移动扣费','活到 500 步','活到 5,000 步','活到 10,000 步'],charge_rows)
        charge_figure=link(root/'docs/research/figures/campaign-018-survival.png')
        charge_report=link(root/'docs/research/campaign-018.md')
        charge_section=f'''<section><h2>18 / 免费移动，也可能灭绝</h2><p>十个新种子，每个种子包含布局、繁殖阈值和移动扣费的八种组合，共八十个世界。全部观察到 10,000 步，前百步另存个体行动和能量账本。</p>{charge_table}<img src="{charge_figure}" alt="全部八十个世界，圆点表示灭绝时间，三角表示万步时仍存活；面板区分布局与移动扣费。" style="width:100%;height:auto"><p>成片食物、阈值 40、零移动扣费下，种子 1501、1502、1504 仍分别在 169、118、190 步灭绝；对应高阈值世界均活到万步。因此正的移动扣费不是本设计全部失败的必要条件。</p><p class="small">取消扣费没有取消移动或空间占据，也会改变能量、繁殖和后续随机轨迹。它改善了这批低阈值世界的存活，却没有保证存活，也未确定唯一机制。八十次执行对应十组配对种子，三角不是永久存活。<a href="{charge_report}">完整报告、逐世界结果及预定早期过程</a>。旧十七轮归档与第二版观测补充包尚未包含本轮。</p></section>'''
        page=page.replace('<section><h2>复核与恢复</h2>',charge_section+'<section><h2>复核与恢复</h2>')
    if args.campaigns >= 19:
        records=campaigns[18]
        treatments=[f'{a}-{t}-{c}' for a in ('block',) for t in (40,160) for c in (0,4)]
        require_run_grid([{**r,'treatment':f"{r['arm']}-{r['birth_threshold']}-{r['birth_cost']}"} for r in records],treatments,range(1600,1610))
        root=Path(__file__).resolve().parents[1]
        verification=json.loads((root/'docs/research/results/campaign-019-verification.json').read_text(encoding='utf-8'))
        key=lambda r:(r['arm'],r['birth_threshold'],r['birth_cost'],r['seed'])
        if sorted(records,key=key)!=sorted(verification['runs'],key=key):
            raise ValueError('Joint-zero-charge records differ from independent verification')
        charge_rows=[]
        for arm,label in (('block','成片'),):
            for threshold in (40,160):
                for cost in (0,4):
                    selected=[r for r in records if (r['arm'],r['birth_threshold'],r['birth_cost'])==(arm,threshold,cost)]
                    charge_rows.append([label,threshold,cost,
                        f"{sum(r['population_at_500']>0 for r in selected)}/10",
                        f"{sum(r['population_at_5000']>0 for r in selected)}/10",
                        f"{sum(r['population']>0 for r in selected)}/10"])
        charge_table=table(['食物布局','繁殖阈值','出生扣费','活到 500 步','活到 5,000 步','活到 10,000 步'],charge_rows)
        charge_figure=link(root/'docs/research/figures/campaign-019-survival.png')
        charge_report=link(root/'docs/research/campaign-019.md')
        charge_section=f'''<section><h2>19 / 移动与出生都免费，仍可能灭绝</h2><p>十个新种子，每个包含繁殖阈值与出生扣费的四种组合，共四十个世界。移动扣费始终为零，基础消耗仍为每个体每步 1。</p>{charge_table}<img src="{charge_figure}" alt="全部四十个世界：圆点为灭绝时间，三角为万步时仍存活；左右面板为出生扣费零和四，颜色区分繁殖阈值。" style="width:100%;height:auto"><p>两种直接扣费都为零时，低阈值组 4/10 灭绝，高阈值组全部活到万步。这排除了至少一种正直接扣费作为本设计所有失败的必要条件。</p><p>低阈值的扣费配对中，五组双方存活、一组仅免费存活、两组仅收费存活、两组双方灭绝。免除费用不能保证每个世界都改善；免费出生仍分割亲代能量、占据空间并增加后续基础需求。</p><p class="small">十组初始配对的后续轨迹可以分化。终点存活不等于永久存活，过程差异尚未确定唯一灭绝机制。<a href="{charge_report}">完整四十个结局、早期过程与核验说明</a>。十八轮固定下载包尚不包含本轮。</p></section>'''
        page=page.replace('<section><h2>复核与恢复</h2>',charge_section+'<section><h2>复核与恢复</h2>')
    if args.campaigns >= 20:
        records=campaigns[19]
        labels={'frequent-small':'频繁少量','reference':'基准','rare-large':'稀疏大量'}
        treatments=[f'{t}-{n}' for t in (40,160) for n in labels]
        require_run_grid([{**r,'treatment':f"{r['birth_threshold']}-{r['renewal']}"} for r in records],treatments,range(1700,1710))
        root=Path(__file__).resolve().parents[1]
        verification=json.loads((root/'docs/research/results/campaign-020-verification.json').read_text(encoding='utf-8'))
        key=lambda r:(r['arm'],r['birth_threshold'],r['renewal'],r['seed'])
        if sorted(records,key=key)!=sorted(verification['runs'],key=key):
            raise ValueError('Renewal records differ from independent verification')
        renewal_rows=[]
        for threshold in (40,160):
            for renewal,label in labels.items():
                selected=[r for r in records if (r['birth_threshold'],r['renewal'])==(threshold,renewal)]
                renewal_rows.append([threshold,label,
                    f"{sum(r['population_at_500']>0 for r in selected)}/10",
                    f"{sum(r['population_at_5000']>0 for r in selected)}/10",
                    f"{sum(r['population']>0 for r in selected)}/10"])
        renewal_table=table(['繁殖阈值','补给方式','活到 500 步','活到 5,000 步','活到 10,000 步'],renewal_rows)
        renewal_figure=link(root/'docs/research/figures/campaign-020-survival.png')
        renewal_report=link(root/'docs/research/campaign-020.md')
        renewal_section=f'''<section><h2>20 / 相同名义平均补给，不同到达方式</h2><p>十个新种子，每个包含三种补给方式与两种繁殖阈值，共六十个世界。频繁少量、基准、稀疏大量的每格每步名义平均补给均为 0.06；移动和出生直接扣费均为零。</p>{renewal_table}<img src="{renewal_figure}" alt="全部六十个世界，三个面板区分补给方式；圆点为灭绝，三角为万步右删失，颜色区分繁殖阈值。" style="width:100%;height:auto"><p>低阈值下，稀疏大量与基准既有仅前者存活，也有仅后者存活的种子，未形成每个种子都受益的排序。高阈值三组全部存活。</p><p class="small">资源容量和摄食上限使实际供给并不相同，不能把差异解释为纯波动效应。所有世界均继续计算至一万步，灭绝后的补给不代表供应给活种群。<a href="{renewal_report}">完整配对结果、实际供给与摄食检查点及早期过程核验</a>。十九轮固定下载包尚未包含本轮。</p></section>'''
        page=page.replace('<section><h2>复核与恢复</h2>',renewal_section+'<section><h2>复核与恢复</h2>')
    if args.campaigns >= 21:
        records=campaigns[20]
        labels={'frequent-small':'频繁少量','reference':'基准','rare-large':'稀疏大量'}
        treatments=[f'{t}-{n}-{c}' for t in (40,160) for n in labels for c in (24,96)]
        require_run_grid([{**r,'treatment':f"{r['birth_threshold']}-{r['renewal']}-{r['food_capacity']}"} for r in records],treatments,range(1800,1810))
        root=Path(__file__).resolve().parents[1]
        verification=json.loads((root/'docs/research/results/campaign-021-verification.json').read_text(encoding='utf-8'))
        key=lambda r:(r['arm'],r['birth_threshold'],r['renewal'],r['food_capacity'],r['seed'])
        if sorted(records,key=key)!=sorted(verification['runs'],key=key):
            raise ValueError('Buffer-capacity records differ from independent verification')
        capacity_rows=[]
        for threshold in (40,160):
            for renewal,label in labels.items():
                for capacity in (24,96):
                    selected=[r for r in records if (r['birth_threshold'],r['renewal'],r['food_capacity'])==(threshold,renewal,capacity)]
                    capacity_rows.append([threshold,label,capacity,
                        f"{sum(r['population_at_500']>0 for r in selected)}/10",
                        f"{sum(r['population_at_5000']>0 for r in selected)}/10",
                        f"{sum(r['population']>0 for r in selected)}/10"])
        capacity_table=table(['繁殖阈值','补给方式','容量','活到 500 步','活到 5,000 步','活到 10,000 步'],capacity_rows)
        capacity_figure=link(root/'docs/research/figures/campaign-021-survival.png')
        capacity_report=link(root/'docs/research/campaign-021.md')
        capacity_section=f'''<section><h2>21 / 更大的容量，没有一致改善存活</h2><p>十个新种子，每个包含两种容量、两种繁殖阈值与三种补给方式，共120个世界。容量从24增至96，初始食物仍为同一地图上的5,120单位，初始个体与随机状态保持配对。</p>{capacity_table}<img src="{capacity_figure}" alt="全部120个世界的容量配对结局；六个面板区分阈值与补给方式，颜色区分容量，圆点为灭绝，三角为万步右删失。" style="width:100%;height:auto"><p>低阈值下，三种补给方式的大容量净配对存活优势为 +1、−2、−4，未支持预登记的三组均为正的预测。三组均存在仅小容量存活的种子。高阈值的六十个世界全部活到观察终点。</p><p class="small">增加容量会改变储存、摄食与后续轨迹，不能把结果单独归因为容量损耗。灭绝后的补给与生存期间补给分开记录；终点存活不表示永久存活。<a href="{capacity_report}">全部配对结局、资源窗口与独立核验</a>。二十轮固定下载包不含本轮。</p></section>'''
        page=page.replace('<section><h2>复核与恢复</h2>',capacity_section+'<section><h2>复核与恢复</h2>')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(page)
    print(args.output.resolve())


if __name__ == "__main__":
    main()

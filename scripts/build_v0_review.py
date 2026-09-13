"""Build a local Chinese review page from completed campaign artifacts."""

import argparse
from collections import defaultdict
from html import escape
import json
import os
from pathlib import Path
from statistics import mean
from urllib.parse import quote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("data/review-v0-8.html"))
    args = parser.parse_args()
    campaigns = [json.loads((args.data_root / f"campaign-{i:03d}" / "results.json").read_text(encoding="utf-8"))
                 for i in range(1, 9)]
    if [len(c) for c in campaigns] != [10, 100, 80, 20, 30, 50, 60, 20]:
        raise ValueError("Expected complete campaigns 001–008")
    for i in range(2, 9):
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(page)
    print(args.output.resolve())


if __name__ == "__main__":
    main()

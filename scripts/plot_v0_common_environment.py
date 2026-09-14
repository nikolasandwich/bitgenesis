"""Show all source-level common-environment contrasts after complete verification."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
if __package__:
    from .verify_v0_common_environment_histories import source_contrasts
else:
    from verify_v0_common_environment_histories import source_contrasts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--histories', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in ('.png', '.svg', '.json')]
    if any(p.exists() for p in targets):
        raise FileExistsError('Choose a new figure prefix')
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    metrics, history = load(args.metrics), load(args.histories)
    manifest_path = Path(__file__).resolve().parents[1]/'docs/research/results/campaign-023-samples.json'
    manifest = load(manifest_path)
    samples = {s['source_seed']: s['selected'] for s in manifest['samples'] if s['available']}
    if (history['metric_verification_sha256'] != sha(args.metrics)
            or metrics['manifest_sha256'] != sha(manifest_path)
            or history['available_sources'] != len(samples)):
        raise ValueError('Full verification linkage differs')
    comparison = source_contrasts(metrics['runs'], set(samples))
    if any(history[k] != v for k, v in comparison.items()):
        raise ValueError('Source contrasts differ from complete evaluation records')
    if not samples:
        raise ValueError('No available source to plot')
    rows = comparison['sources']
    fig, (ax, contrast) = plt.subplots(1, 2, figsize=(12, 11), sharey=True,
                                     gridspec_kw={'width_ratios': [1.3, 1]})
    fig.subplots_adjust(left=.23, right=.96, bottom=.16, top=.82, wspace=.22)
    for y, row in enumerate(rows):
        if y % 2 == 0:
            for panel in (ax, contrast):
                panel.axhspan(y-.5, y+.5, color='#f3f4ef', zorder=0)
        counts = row['counts']
        for arm, offset, color in (('sampled', -.15, '#277e74'), ('ancestor', .15, '#bb6c32')):
            survivors = counts['both_alive'] + counts[f'{arm}_only']
            ax.scatter(survivors, y+offset, color=color, s=38,
                       label=arm.capitalize() if y == 0 else None, zorder=3)
        value = row['contrast_float']
        contrast.hlines(y, 0, value, color='#546879', linewidth=2)
        contrast.scatter(value, y, color='#546879', s=30, zorder=3)
        contrast.annotate(row['contrast'], (value, y), xytext=(7, 0),
                          textcoords='offset points', va='center', fontsize=9)
    labels = [f"{r['source_seed']}   {samples[r['source_seed']]['genome']} / "
              f"{samples[r['source_seed']]['founder_genome']}" for r in rows]
    ax.set_yticks(range(len(rows)), labels)
    ax.set_ylim(len(rows)-.5, -.5)
    ax.set_xlim(-.3, 5.3)
    ax.set_xticks(range(6))
    ax.set_xlabel('Worlds alive at tick 10,000 (out of five)')
    ax.set_ylabel('Source seed   sampled / ancestor trait')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, 1.01), ncol=2, frameon=False)
    contrast.set_xlim(-1.1, 1.3)
    contrast.set_xticks([-1, -.5, 0, .5, 1])
    contrast.axvline(0, color='#999999', linewidth=.8)
    contrast.set_xlabel('Paired survival contrast within source')
    for panel in (ax, contrast):
        panel.grid(axis='x', alpha=.18)
        panel.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Early sampled traits versus their founding ancestors', fontsize=18, y=.96)
    fig.text(.5, .915, f"Campaign 023 | {len(rows)} sources | five paired evaluation seeds per source",
             ha='center', fontsize=11)
    fig.text(.5, .88, f"Mean source contrast: {comparison['mean_source_contrast']} | "
             f"Positive / zero / negative sources: {comparison['positive_sources']} / "
             f"{comparison['zero_sources']} / {comparison['negative_sources']}", ha='center', fontsize=11)
    fig.text(.5, .09, 'Contrast = (sampled-only survivors - ancestor-only survivors) / 5.',
             ha='center', fontsize=10)
    fig.text(.5, .055, 'All available sources retained, including unchanged traits. Repeats are not independent evolved samples.',
             ha='center', fontsize=9)
    fig.text(.5, .025, 'Finite-horizon fixed-trait assay; no significance or selection-mediated adaptation claim.',
             ha='center', fontsize=9)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in targets[:2]:
        fig.savefig(path, dpi=180)
    plt.close(fig)
    report = dict(**comparison, samples=samples, runs=metrics['runs'],
                  metric_report_sha256=sha(args.metrics), history_report_sha256=sha(args.histories),
                  manifest_sha256=sha(manifest_path), script_sha256=sha(Path(__file__)))
    targets[2].write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()

"""Optional Matplotlib rendering of the verified, archived population paths."""
import json
from pathlib import Path
from hashlib import sha256
from fractions import Fraction
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt, font_manager


def main():
    source=Path('docs/research/results/v4-study-012-population-paths-summary.json')
    proof=json.loads(Path('docs/research/results/v4-study-012-population-paths-independent-verification.json').read_text())
    assert sha256(source.read_bytes()).hexdigest()==proof['summary_sha256']
    groups=json.loads(source.read_text())['groups']
    font=next((name for name in ('Arial Unicode MS','PingFang SC','Noto Sans CJK SC') if any(f.name==name for f in font_manager.fontManager.ttflist)),None)
    if font is None:raise RuntimeError('Chinese font required; install Noto Sans CJK SC or use a system Chinese font')
    plt.rcParams.update({'font.family':font,'axes.unicode_minus':False,'font.size':10,'axes.titlesize':12,'axes.labelsize':10,'savefig.facecolor':'#fbfbfd'})
    fig,axes=plt.subplots(2,2,figsize=(12.8,8.8),layout='constrained',facecolor='#fbfbfd')
    for g,color in zip(groups,('#2464ad','#c15c20')):
        x=[p['tick'] for p in g['path']];label=f"突变 {g['mutation']}"
        y=lambda metric,field:[float(Fraction(p['metrics'][metric][field])) for p in g['path']]
        axes[0,0].plot(x,y('occupied','on'),color=color,label=label+' · 开启')
        axes[0,0].plot(x,y('occupied','off'),color=color,linestyle='--',label=label+' · 关闭')
        axes[0,1].plot(x,y('occupied','difference'),color=color,label=label)
        for field,style,name in (('births','-','累计形成'),('deaths','--','累计消解')):
            axes[1,0].plot(x,y(field,'difference'),color=color,linestyle=style,label=label+' · '+name)
        for field,style,name in (('original_survivors','-','原成员'),('new_survivors','--','新生成员')):
            axes[1,1].plot(x,y(field,'difference'),color=color,linestyle=style,label=label+' · '+name)
    titles=('全世界占据数：关闭分支后期更高','占据均差：早期为正，百步终点为负','事件均差：减少形成，也减少消解','存活成员均差：原成员与新生成员分开')
    for i,(ax,title) in enumerate(zip(axes.flat,titles)):
        ax.set_title(title,loc='left',pad=12);ax.set_xlabel('相对分支步');ax.set_xlim(0,100);ax.set_xticks([0,10,25,50,75,100]);ax.set_facecolor('white');ax.grid(alpha=.18);ax.spines[['top','right']].set_visible(False)
        ax.set_ylabel('单元数' if i==0 else '开启 − 关闭（单元数）')
        if i:ax.axhline(0,color='#606570',linewidth=.9)
        ax.legend(frameon=False,fontsize=8.5,ncol=2 if i!=1 else 1,loc='best')
    fig.suptitle('交换效应随时间变化：同一全世界人口指标的完整路径\n旧轨迹事后核查 · 每条件20配对 · 四锚点后五来源等权 · 无新增模拟',fontsize=15)
    folder=Path('docs/research/figures');folder.mkdir(exist_ok=True)
    outputs=[]
    for suffix in ('png','svg'):
        target=folder/f'v4-study-012-population-paths.{suffix}';fig.savefig(target,dpi=170);outputs.append(target)
    plt.close(fig)
    metadata=dict(source_sha256=sha256(source.read_bytes()).hexdigest(),script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),matplotlib_version=matplotlib.__version__,font=font,outputs={str(p):sha256(p.read_bytes()).hexdigest() for p in outputs})
    (folder/'v4-study-012-population-paths-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()

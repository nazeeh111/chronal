"""Source-bound chronological boundaries, complete equity paths and a real simulated fill."""
from pathlib import Path
import json,math,html
P=Path(__file__).parent;R=P/'worked-run';load=lambda n:json.loads((R/n).read_text());dev=load('development/results.json');held=load('holdout/results.json');plan=load('plan.json');winner=dev['winner'];sim=held['results'][winner]['simulation'];fill=sim['fills'][0];notional=fill['quantity']*fill['price'];reference=fill['quantity']*fill['reference_price'];fee=fill['commission'];assert abs(sim['initial_cash']-notional-fee-fill['cash_after'])<1e-8
fits=dev['results']['ridge20']['fit_records'];assert all(max(f['model']['training_label_end_indices'])<f['train_end']for f in fits)
data={'plan':plan,'winner':winner,'development':{k:v['simulation']for k,v in dev['results'].items()if k in[winner,'equal']},'holdout':{k:v['simulation']for k,v in held['results'].items()},'metrics':{'development':dev['results'][winner]['metrics'],'holdout':held['results'][winner]['metrics'],'holdout_baseline':held['results']['equal']['metrics']},'ridge_cutoffs':[{'exclusive':f['train_end'],'latest_label':max(f['model']['training_label_end_indices'])}for f in fits],'first_holdout_fill':fill,'reference_notional':reference,'execution_notional':notional};(P/'figure-data.json').write_text(json.dumps(data,indent=2)+'\n')
def make(mobile):
 W,H=(420,1110)if mobile else(1160,820);o=[];add=o.append
 def text(x,y,s,size=15,c='#243540',weight=400):add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" font-weight="{weight}">{html.escape(str(s))}</text>')
 def line(x,y,X,Y,c='#c7c9c3',w=1,dash=''):add(f'<line x1="{x:.8f}" y1="{y:.8f}" x2="{X:.8f}" y2="{Y:.8f}" stroke="{c}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"'if dash else'')+'/>')
 desc='A fictional-price experiment selects trend60 using development only. Its development return is positive, but its separate holdout loses money; the equal-weight baseline also loses. Both complete equity paths include initial capital and all marked sessions. Each region starts a separate 100000-unit account, while cash persists across folds inside that region. The first holdout buy shows reference notional, adverse execution, commission and remaining cash. Train-only ridge label endpoints remain before every exclusive cutoff.'
 add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc"><title id="title">Selection is not a profit</title><desc id="desc">{desc}</desc><style>text{{font-family:Arial,"DejaVu Sans",sans-serif}}</style><rect width="100%" height="100%" fill="#f4f0e7"/>')
 text(28,34,'Chronal / fictional prices, simulated trades',13,'#596874');text(28,78,'Selection is',32,'#162a35',600);text(28,116,'not a profit.',32,'#162a35',600)
 tx,ty,tw=28,170,W-56
 text(tx,ty-16,'Freeze the choice before opening the holdout.',14,'#162a35',600)
 segments=[('Initial train',0,252,'#ced5d1'),('Development',254,630,'#b1c7b8'),('Holdout',630,756,'#e2c498')]
 for label,a,b,c in segments:add(f'<rect data-range="{label}" x="{tx+a/756*tw:.8f}" y="{ty}" width="{(b-a)/756*tw:.8f}" height="18" fill="{c}"/>')
 text(tx,ty+40,'252 train + 2 gap; 376 development; 126 holdout.',12,'#596874');text(tx,ty+61,'6 expanding development fits; labels end before cutoffs.',12,'#596874')
 text(tx,ty+82,'First ridge cutoff 252; latest training label 251.',12,'#596874')
 limits=(85,120)
 for ri,(region,record)in enumerate([('development',dev),('holdout',held)]):
  px,py,pw,ph=(48,335+ri*310,344,180)if mobile else(62+ri*555,340,490,220)
  text(px,py-35,region.capitalize()+f' / {len(record["results"][winner]["simulation"]["equity"])} sessions',17,'#162a35',600)
  X=lambda i,n:px+i/(n-1)*pw;Y=lambda v:py+ph-(v-limits[0])/(limits[1]-limits[0])*ph
  for tick in[90,100,110,120]:line(px,Y(tick),px+pw,Y(tick));text(px-32,Y(tick)+4,str(tick),11,'#596874')
  for name,c in [('equal','#986919'),(winner,'#156c5c')]:
   s=record['results'][name]['simulation'];values=[100]+[100*v/s['initial_cash']for v in s['equity']];points=[(X(i,len(values)),Y(v))for i,v in enumerate(values)];add(f'<polyline data-series="{region}-{name}" points="'+' '.join(f'{x:.8f},{y:.8f}'for x,y in points)+f'" fill="none" stroke="{c}" stroke-width="{2 if name==winner else 1.4}"'+(' stroke-dasharray="5 3"'if name=='equal'else'')+'/>')
  indices=record['results'][winner]['simulation']['indices'];text(px,py+ph+15,f'Before session {indices[0]}',11,'#596874');text(px+pw-24,py+ph+15,str(indices[-1]),11,'#596874')
  ret=record['results'][winner]['metrics']['total_return']*100;text(px,py+ph+36,f'{winner}: {ret:+.3f}%',16,'#156c5c'if ret>0 else'#a23b34',600);text(px,py+ph+56,'Solid: selected. Dashed: equal weight.',12,'#596874');text(px,py+ph+74,'Separate account starts at 100; net of execution.',11,'#596874')
 ay=960 if mobile else 680
 text(28,ay,'The first holdout buy has to pay its way.',16,'#162a35',600)
 text(28,ay+28,f'{reference:,.2f} reference → {notional:,.2f} executed',15,'#243540',600)
 text(28,ay+54,f'+ {fee:.4f} commission → {fill["cash_after"]:,.4f} cash left',14,'#243540',600)
 text(28,ay+80,'Decision after close 630; fill at the later open 631.',12,'#596874')
 text(28,H-20,'One fictional run. No live orders or investable-edge claim.',12,'#596874');add('</svg>');(P/('chronology-mobile.svg'if mobile else 'chronology.svg')).write_text(''.join(o))
make(False);make(True)

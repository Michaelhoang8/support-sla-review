
from pathlib import Path
import base64, csv, hashlib, json, random, sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
for folder in ['data/raw','data/clean','analysis','sql','docs/charts','docs/screenshots','docs/recordings','tests']:
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#d5dcd9','axes.labelcolor':'#42554e','xtick.color':'#42554e','ytick.color':'#42554e','figure.facecolor':'#fafbf8','axes.facecolor':'#fafbf8','axes.titleweight':'bold','axes.titlelocation':'left','axes.titlepad':20,'font.size':11,'savefig.dpi':170})
def write_csv(df,path): df.to_csv(ROOT/path,index=False,lineterminator='\n')
def export(fig,name):
    fig.text(.01,.012,'Synthetic portfolio study | Reproduce: python scripts/build.py',fontsize=8,color='#667770')
    fig.savefig(ROOT/f'docs/charts/{name}.png',bbox_inches='tight')
    fig.savefig(ROOT/f'docs/charts/{name}.svg',bbox_inches='tight')
    plt.close(fig)
def query(name,sql):
    (ROOT/f'sql/{name}.sql').write_text(sql.strip()+'\n',encoding='utf-8')
    out=pd.read_sql_query(sql,db)
    write_csv(out,f'analysis/{name}.csv')
    return out
def finish(qa,findings):
    (ROOT/'analysis/quality_report.json').write_text(json.dumps(qa,indent=2)+'\n')
    (ROOT/'analysis/findings.md').write_text(findings,encoding='utf-8')
    import nbformat as nbf
    nb=nbf.v4.new_notebook()
    nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
    nb.cells=[nbf.v4.new_markdown_cell('# '+TITLE+'\n\nSynthetic data. This notebook executes the checked-in SQL against the rebuilt SQLite warehouse. See the decision memo for interpretation and limitations.'),nbf.v4.new_code_cell("from pathlib import Path\nimport sqlite3, pandas as pd\nroot=Path.cwd()\nif root.name=='analysis': root=root.parent\nconnection=sqlite3.connect(root/'analysis/warehouse.sqlite3')")]
    for f in sorted((ROOT/'sql').glob('*.sql')):
        nb.cells.extend([nbf.v4.new_markdown_cell('## '+f.stem.replace('_',' ').title()),nbf.v4.new_code_cell(f"pd.read_sql_query((root/'sql/{f.name}').read_text(),connection)")])
    nb.cells.append(nbf.v4.new_code_cell('connection.close()'))
    from nbclient import NotebookClient
    NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
    nbf.write(nb,ROOT/'analysis/analysis.ipynb')
    manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['data/raw','data/clean'] for p in sorted((ROOT/folder).glob('*.csv'))}
    (ROOT/'analysis/data_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    db.close()

TITLE='Customer support SLA review'
rng=random.Random(90531);snapshot=pd.Timestamp('2026-01-01T00:00:00')
teams=pd.DataFrame([{'team_id':i+1,'team':name,'specialty':specialty} for i,(name,specialty) in enumerate([('General','Account and billing'),('Technical','Product faults'),('Priority','Escalations')])])
priorities=pd.DataFrame([{'priority':p,'response_sla_hours':r,'resolution_sla_hours':s} for p,r,s in [('High',4,24),('Normal',8,72),('Low',24,168)]])
rows=[]
for i in range(6000):
    opened=pd.Timestamp('2025-01-01')+pd.Timedelta(hours=rng.randrange(8760),minutes=rng.randrange(60))
    team=rng.choices([1,2,3],[.5,.35,.15])[0];priority=rng.choices(['High','Normal','Low'],[.2,.6,.2])[0]
    response=rng.lognormvariate(1.0 if team!=2 else 1.7,.85)*(1.5 if opened.month>=10 and team==2 else 1)
    resolution=response+rng.lognormvariate(3.0 if team!=2 else 3.8,.9)
    first=opened+pd.Timedelta(minutes=round(response*60));closed=opened+pd.Timedelta(minutes=round(resolution*60))
    unresolved=rng.random()<.035
    first=None if first>=snapshot else first
    closed=None if closed>=snapshot or unresolved else closed
    survey=closed is not None and rng.random()<(.36 if resolution<72 else .18)
    csat=rng.choices([1,2,3,4,5],[.05,.08,.15,.28,.44] if resolution<72 else [.2,.2,.25,.2,.15])[0] if survey else None
    rows.append({'ticket_id':f'T{i+1:06d}','opened_at':opened.isoformat(),'first_response_at':first.isoformat() if first is not None else '', 'resolved_at':closed.isoformat() if closed is not None else '', 'team_id':team,'priority':priority,'channel':rng.choice(['Email','Chat','Web form']),'csat':csat,'updated_at':snapshot.isoformat()})
raw=pd.DataFrame(rows);older=raw.iloc[:90].copy();older['updated_at']='2025-01-01T00:00:00';older['resolved_at']='';older['csat']=None
bad=raw.iloc[:10].copy();bad['ticket_id']=[f'BAD{i:03d}' for i in range(10)];bad['first_response_at']='2024-01-01T00:00:00'
raw=pd.concat([raw,older,bad],ignore_index=True)
write_csv(raw,'data/raw/ticket_snapshots.csv');write_csv(teams,'data/raw/teams.csv');write_csv(priorities,'data/raw/sla_policy.csv')
latest=raw.sort_values(['ticket_id','updated_at'],kind='stable').drop_duplicates('ticket_id',keep='last').copy()
for c in ['opened_at','first_response_at','resolved_at']: latest[c]=pd.to_datetime(latest[c],errors='coerce')
invalid=(latest.first_response_at<latest.opened_at)|(latest.resolved_at<latest.first_response_at)|latest.opened_at.isna()
quarantine=latest[invalid].copy();quarantine['reason']='Timestamp sequence invalid';write_csv(quarantine,'analysis/quarantine.csv')
fact=latest[~invalid].merge(priorities,on='priority',validate='many_to_one')
fact['month']=fact.opened_at.dt.strftime('%Y-%m');fact['age_hours']=(snapshot-fact.opened_at).dt.total_seconds()/3600
fact['response_hours']=(fact.first_response_at-fact.opened_at).dt.total_seconds()/3600;fact['resolution_hours']=(fact.resolved_at-fact.opened_at).dt.total_seconds()/3600
fact['response_eligible']=((fact.response_hours.notna())|(fact.age_hours>=fact.response_sla_hours)).astype(int)
fact['response_breach']=((fact.response_hours>fact.response_sla_hours)|(fact.response_hours.isna()&(fact.age_hours>=fact.response_sla_hours))).astype(int)
fact['resolution_eligible']=((fact.resolution_hours.notna())|(fact.age_hours>=fact.resolution_sla_hours)).astype(int)
fact['resolution_breach']=((fact.resolution_hours>fact.resolution_sla_hours)|(fact.resolution_hours.isna()&(fact.age_hours>=fact.resolution_sla_hours))).astype(int)
fact['open_flag']=fact.resolved_at.isna().astype(int);fact['overdue_open']=((fact.open_flag==1)&(fact.age_hours>=fact.resolution_sla_hours)).astype(int)
fact['csat_positive']=(fact.csat>=4).astype(int);fact['csat_responded']=fact.csat.notna().astype(int)
fact['age_band']=pd.cut(fact.age_hours,[-1,24,72,168,float('inf')],labels=['01 Under 24h','02 24–72h','03 72h–7d','04 Over 7d']).astype(str)
for name,df in [('tickets',fact),('teams',teams),('sla_policy',priorities)]: write_csv(df,f'data/clean/{name}.csv')
db=sqlite3.connect(ROOT/'analysis/warehouse.sqlite3')
for name,df in [('tickets',fact),('teams',teams),('sla_policy',priorities)]: df.to_sql(name,db,index=False,if_exists='replace')
kpi=query('01_sla_scorecard','''SELECT COUNT(*) tickets,SUM(response_eligible) response_eligible,SUM(response_breach) response_breaches,1.0-SUM(response_breach)*1.0/SUM(response_eligible) response_attainment,SUM(resolution_eligible) resolution_eligible,1.0-SUM(resolution_breach)*1.0/SUM(resolution_eligible) resolution_attainment,SUM(open_flag) open_tickets,SUM(overdue_open) overdue_open,SUM(csat_responded) survey_responses,1.0*SUM(csat_positive)/SUM(csat_responded) csat_positive FROM tickets''')
monthly=query('02_monthly_sla','''SELECT month,COUNT(*) tickets,SUM(response_eligible) eligible,SUM(response_breach) breaches,1.0-SUM(response_breach)*1.0/SUM(response_eligible) attainment FROM tickets GROUP BY month ORDER BY month''')
team=query('03_team_priority','''SELECT d.team,t.priority,COUNT(*) tickets,SUM(response_eligible) eligible,SUM(response_breach) breaches,1.0-SUM(response_breach)*1.0/SUM(response_eligible) response_attainment,SUM(overdue_open) overdue_open FROM tickets t JOIN teams d USING(team_id) GROUP BY d.team,t.priority ORDER BY d.team,t.priority''')
backlog=query('04_backlog_age','''SELECT d.team,t.age_band,COUNT(*) open_tickets,SUM(overdue_open) overdue FROM tickets t JOIN teams d USING(team_id) WHERE t.open_flag=1 GROUP BY d.team,t.age_band ORDER BY d.team,t.age_band''')
survey=query('05_survey_bias','''SELECT CASE WHEN resolution_hours<=72 THEN 'Resolved within 72h' ELSE 'Resolved after 72h' END resolution_group,COUNT(*) resolved_tickets,SUM(csat_responded) responses,1.0*SUM(csat_responded)/COUNT(*) response_rate,1.0*SUM(csat_positive)/NULLIF(SUM(csat_responded),0) positive_rate FROM tickets WHERE open_flag=0 GROUP BY resolution_group ORDER BY resolution_group''')
percentiles=fact.groupby('team_id').response_hours.quantile([.5,.9,.95]).unstack().rename(columns={.5:'p50',.9:'p90',.95:'p95'}).reset_index().merge(teams,on='team_id');write_csv(percentiles,'analysis/06_response_percentiles.csv')
qa={'raw_snapshots':len(raw),'superseded_snapshots_removed':90,'quarantined_tickets':len(quarantine),'clean_tickets':len(fact),'unmatured_response_tickets':int((fact.response_eligible==0).sum()),'unmatured_resolution_tickets':int((fact.resolution_eligible==0).sum()),'snapshot_utc':'2026-01-01T00:00:00','clock':'24x7 calendar hours, not business hours','seed':90531}
fig,ax=plt.subplots(figsize=(12,6));ax.plot(range(12),monthly.attainment*100,color='#3b5b99',lw=3,marker='o');ax.set_xticks(range(12),monthly.month.str[5:]);ax.set_ylim(0,100);ax.set_ylabel('Response SLA attainment %');ax.set_xlabel('2025 opening month');ax.set_title('Response performance across the year',fontsize=23);ax.grid(axis='y',alpha=.2);fig.tight_layout(rect=(0,.04,1,1));export(fig,'01_sla_trend')
fig,ax=plt.subplots(figsize=(12,6));pivot=team.pivot(index='team',columns='priority',values='response_attainment')[['High','Normal','Low']];im=ax.imshow(pivot*100,cmap='YlGnBu',vmin=0,vmax=100,aspect='auto');ax.set_xticks(range(3),['High · 4h','Normal · 8h','Low · 24h']);ax.set_yticks(range(3),pivot.index)
for i in range(3):
    for j in range(3): ax.text(j,i,f'{pivot.iloc[i,j]:.1%}',ha='center',va='center',color='white' if pivot.iloc[i,j]>.6 else '#18283d',fontsize=20)
ax.set_title('Priority mix matters when comparing teams',fontsize=23);fig.colorbar(im,ax=ax,label='Response SLA attainment (%)');fig.tight_layout(rect=(0,.04,1,1));export(fig,'02_team_priority')
fig,ax=plt.subplots(figsize=(12,6));bp=backlog.pivot(index='team',columns='age_band',values='open_tickets').fillna(0);bp.plot.barh(stacked=True,ax=ax,color=['#b6c5e3','#7e9bc7','#4c6d9f','#a65c4b']);ax.legend(title='Calendar age at snapshot',frameon=False,bbox_to_anchor=(1,1));ax.set_title('Open workload includes aged unresolved tickets',fontsize=22);ax.set_xlabel('Open tickets');ax.set_ylabel('');fig.tight_layout(rect=(0,.04,1,1));export(fig,'03_backlog')
fig,ax=plt.subplots(figsize=(12,5));x=np.arange(2);ax.bar(x-.18,survey.response_rate*100,width=.36,color='#3b5b99',label='Survey response rate');ax.bar(x+.18,survey.positive_rate*100,width=.36,color='#c1804f',label='Positive among respondents');ax.set_xticks(x,survey.resolution_group);ax.set_ylim(0,100);ax.set_ylabel('Percent');ax.legend(frameon=False);ax.set_title('CSAT is not representative of every resolved ticket',fontsize=22);fig.tight_layout(rect=(0,.04,1,1));export(fig,'04_survey_bias')
row=kpi.iloc[0];worst=team.sort_values('response_attainment').iloc[0]
findings=f'''# Decision memo: support SLA performance

**Scope:** 6,000 synthetic tickets opened in 2025, observed at 2026-01-01 00:00 UTC. All deadlines use calendar hours, not business-hour calendars.

## Findings

Response SLA attainment is **{row.response_attainment:.1%}** over {int(row.response_eligible):,} eligible tickets. Resolution attainment is {row.resolution_attainment:.1%}. There are {int(row.open_tickets):,} unresolved tickets, including {int(row.overdue_open):,} beyond their priority-specific resolution deadline. The weakest response cell is **{worst.team} / {worst.priority}**, at {worst.response_attainment:.1%} across {int(worst.eligible):,} eligible tickets.

## Proposed decision

Review Technical-team routing, staffing and escalation coverage, especially late-year high-priority demand. Compare within priority before ranking teams; raw team averages mix different deadlines and workloads. Establish a daily overdue-backlog review and test a routing intervention with matched priority and channel strata.

## Denominators and censoring

A ticket is eligible once an outcome is observed or its deadline has elapsed. An unresolved/unanswered ticket past its deadline counts as a breach. Pending tickets still within the deadline are excluded, never counted as successes. An observed response exactly at the deadline meets SLA; pending at the deadline is operationally overdue at snapshot. Month is opening month, not response month. Recent cohorts may remain unstable. P50/P90/P95 response times describe observed responses only; they do not replace the censored SLA measure.

CSAT positivity is {row.csat_positive:.1%} among {int(row.survey_responses):,} respondents. Survey response rates differ by resolution speed; the score cannot be generalized to all customers. No missing CSAT value is filled with zero.

## Data quality

6,100 raw snapshot rows → keep the latest snapshot for each ticket (90 superseded rows removed) → quarantine 10 responses occurring before opening → 6,000 unique tickets. All IDs and timestamps are fictional. Timestamp monotonicity, denominator membership, overdue inclusion and dimension integrity are checked before publication.

## Limitations

The generator intentionally includes a late-year Technical-team slowdown. Findings are simulated and do not prove staffing caused a real decline. Reopens, reassignment, holidays, customer-wait pauses and event-level history are absent. Production SLA calculations would require contractual calendar and pause rules. Proposed improvements are hypotheses, not achieved impact.
'''
finish(qa,findings)

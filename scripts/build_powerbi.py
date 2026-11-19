"""Build portable Power BI semantic models and report visuals from clean CSVs.

Run from a project: python scripts/build_powerbi.py
The scaffolded report shell is committed; no CLI is required to regenerate visuals.
"""
from pathlib import Path
import base64, hashlib, json
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RETAIL='retail' in ROOT.name
NAME='RetailMargin' if RETAIL else 'SupportSLA'
FACT='orders' if RETAIL else 'tickets'
ACCENT='#246857' if RETAIL else '#365b91'
REPORT=ROOT/'powerbi'/f'{NAME}.Report'
MODEL=ROOT/'powerbi'/f'{NAME}.SemanticModel'
MODEL.mkdir(exist_ok=True)
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def uid(s): return hashlib.sha256(s.encode()).hexdigest()[:20]
def expr(value):
    v=('true' if value else 'false') if isinstance(value,bool) else (str(value)+'D' if isinstance(value,(int,float)) else "'"+value.replace("'","''")+"'")
    return {'expr':{'Literal':{'Value':v}}}
def color(v): return {'solid':{'color':expr(v)}}
def props(**kw): return [{'properties':kw}]

if RETAIL:
    measures={
        'Orders':('COUNTROWS(orders)','#,0'),
        'Net revenue':('DIVIDE(SUM(orders[net_revenue_cents]),100)','$#,0'),
        'Contribution':('DIVIDE(SUM(orders[contribution_cents]),100)','$#,0'),
        'Contribution margin':('DIVIDE([Contribution],[Net revenue])','0.0%'),
        'Unit return rate':('DIVIDE(SUM(orders[returned_units]),SUM(orders[quantity]))','0.0%'),
        'Discounts':('DIVIDE(SUM(orders[discount_cents]),100)','$#,0'),
        'Refunds':('DIVIDE(SUM(orders[refund_cents]),100)','$#,0'),
        'Gross sales':('DIVIDE(SUM(orders[gross_sales_cents]),100)','$#,0'),
    }
    rels=[('product_id','products','product_id'),('customer_id','customers','customer_id')]
else:
    measures={
        'Tickets':('COUNTROWS(tickets)','#,0'),
        'Response eligible':('SUM(tickets[response_eligible])','#,0'),
        'Response breaches':('SUM(tickets[response_breach])','#,0'),
        'Response SLA':('DIVIDE([Response eligible]-[Response breaches],[Response eligible])','0.0%'),
        'Resolution SLA':('DIVIDE(SUM(tickets[resolution_eligible])-SUM(tickets[resolution_breach]),SUM(tickets[resolution_eligible]))','0.0%'),
        'Open tickets':('SUM(tickets[open_flag])','#,0'),
        'Overdue open':('SUM(tickets[overdue_open])','#,0'),
        'Survey responses':('SUM(tickets[csat_responded])','#,0'),
        'Positive CSAT':('DIVIDE(SUM(tickets[csat_positive]),[Survey responses])','0.0%'),
    }
    rels=[('team_id','teams','team_id'),('priority','sla_policy','priority')]
tables=[]
dictionary=[]
for path in sorted((ROOT/'data/clean').glob('*.csv')):
    name=path.stem;df=pd.read_csv(path)
    columns=[];mtypes=[]
    for c in df:
        numeric=pd.api.types.is_numeric_dtype(df[c]);integer=numeric and df[c].dropna().mod(1).eq(0).all()
        dtype='int64' if integer else 'double' if numeric else 'string'
        columns.append({'name':c,'dataType':dtype,'sourceColumn':c,'summarizeBy':'none'})
        mtypes.append('{"'+c+'",'+('Int64.Type' if integer else 'type number' if numeric else 'type text')+'}')
        dictionary.append({'table':name,'column':c,'type':dtype,'nulls':int(df[c].isna().sum()),'distinct':int(df[c].nunique())})
    data=base64.b64encode(path.read_bytes()).decode()
    m='let\n Source=Csv.Document(Binary.FromText("'+data+'",BinaryEncoding.Base64),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]),\n Headers=Table.PromoteHeaders(Source,[PromoteAllScalars=true]),\n Nulls=Table.ReplaceValue(Headers,"",null,Replacer.ReplaceValue,Table.ColumnNames(Headers)),\n Typed=Table.TransformColumnTypes(Nulls,{'+','.join(mtypes)+'},"en-US")\nin Typed'
    table={'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':m.splitlines()}}]}
    if name==FACT: table['measures']=[{'name':k,'expression':v[0],'formatString':v[1]} for k,v in measures.items()]
    tables.append(table)
    (ROOT/f'powerbi/{name}.pq').write_text(m,encoding='utf-8')
pd.DataFrame(dictionary).to_csv(ROOT/'analysis/data_dictionary.csv',index=False)
save(MODEL/'definition.pbism',{'version':'1.0','settings':{}})
save(MODEL/'model.bim',{'name':NAME,'compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','tables':tables,'relationships':[{'name':uid(str(r)),'fromTable':FACT,'fromColumn':r[0],'toTable':r[1],'toColumn':r[2],'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection'} for r in rels],'annotations':[{'name':'PBI_QueryOrder','value':json.dumps([t['name'] for t in tables])}]}})
(ROOT/'powerbi/measures.dax').write_text('\n\n'.join(f'// Format: {v[1]}\n{k} = {v[0]}' for k,v in measures.items())+'\n',encoding='utf-8')

SCHEMA='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
page_meta=json.loads((REPORT/'definition/pages/pages.json').read_text())
first=page_meta['pageOrder'][0];second=uid(NAME+'details')
save(REPORT/'definition/pages/pages.json',{'$schema':SCHEMA+'pagesMetadata/1.1.0/schema.json','pageOrder':[first,second],'activePageName':first})
def page(pid,title):
    save(REPORT/f'definition/pages/{pid}/page.json',{'$schema':SCHEMA+'page/2.1.0/schema.json','name':pid,'displayName':title,'displayOption':'FitToPage','height':800,'width':1280,'objects':{'background':props(color=color('#f5f6f2'),transparency=expr(0))}})
def visual(pid,key,kind,x,y,w,h,title=None):
    vid=uid(pid+key)
    v={'$schema':SCHEMA+'visualContainer/2.9.0/schema.json','name':vid,'position':{'x':x,'y':y,'z':1000,'width':w,'height':h,'tabOrder':int(x+y)},'visual':{'visualType':kind,'visualContainerObjects':{'background':props(show=expr(True),color=color('#FFFFFF'),transparency=expr(0)),'border':props(show=expr(False))}}}
    if title: v['visual']['visualContainerObjects']['title']=props(show=expr(True),text=expr(title),fontSize=expr(12),fontColor=color('#283d35'))
    return v
def emit(pid,v): save(REPORT/f'definition/pages/{pid}/visuals/{v["name"]}/visual.json',v)
def projection(table,field,measure=False):
    return {'field':{('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':field}},'queryRef':table+'.'+field,'nativeQueryRef':field}
def text(pid,key,title,subtitle):
    v=visual(pid,key,'textbox',28,18,1224,82)
    v['visual']['objects']={'general':props(paragraphs=[{'textRuns':[{'value':title,'textStyle':{'fontFamily':'Segoe UI Semibold','fontSize':'28px','color':ACCENT}}]},{'textRuns':[{'value':subtitle,'textStyle':{'fontFamily':'Segoe UI','fontSize':'12px','color':'#52625d'}}]}])}
    v['visual']['visualContainerObjects']['background']=props(show=expr(False));emit(pid,v)
def card(pid,i,name):
    v=visual(pid,name,'card',28+i*246,112,230,102)
    v['visual']['query']={'queryState':{'Values':{'projections':[projection(FACT,name,True)]}}}
    v['visual']['objects']={'labels':props(fontSize=expr(28),color=color(ACCENT)),'categoryLabels':props(show=expr(True),fontSize=expr(11))};emit(pid,v)
def chart(pid,key,kind,x,y,w,h,table,field,measure,title,series=None):
    v=visual(pid,key,kind,x,y,w,h,title)
    p=projection(table,field);p['active']=True
    v['visual']['query']={'queryState':{'Category':{'projections':[p]},'Y':{'projections':[projection(FACT,measure,True)]}},'sortDefinition':{'sort':[{'field':p['field'],'direction':'Ascending'}],'isDefaultSort':True}}
    if series: v['visual']['query']['queryState']['Series']={'projections':[projection(*series)]}
    v['visual']['objects']={'dataPoint':props(defaultColor=color(ACCENT)),'categoryAxis':props(fontSize=expr(10)),'valueAxis':props(fontSize=expr(10))}
    if series: v['visual']['objects'].pop('dataPoint')
    if kind=='lineChart': v['visual']['objects']['lineStyles']=props(lineChartType=expr('linear'))
    v['visual']['visualContainerObjects']['subTitle']=props(show=expr(False))
    emit(pid,v)
def slicer(pid,table,field):
    v=visual(pid,'slice'+field,'slicer',1012,230,240,245,'Filter '+field)
    v['visual']['query']={'queryState':{'Values':{'projections':[projection(table,field)]}}}
    v['visual']['objects']={'selection':props(singleSelect=expr(False))};emit(pid,v)

if RETAIL:
    page(first,'Margin overview');text(first,'title','Retail margin | 2024–2025','Synthetic study · USD · Select a category or year to cross-filter · Contribution excludes overhead and tax')
    for i,m in enumerate(['Net revenue','Contribution','Contribution margin','Unit return rate','Orders']):card(first,i,m)
    chart(first,'trend','lineChart',28,230,622,245,'orders','month','Net revenue','Net revenue by order month')
    chart(first,'category','clusteredBarChart',670,230,320,245,'products','category','Contribution','Contribution by category');slicer(first,'orders','year')
    chart(first,'margin','lineChart',28,495,622,275,'orders','month','Contribution margin','Margin trend · ratio of sums')
    chart(first,'regions','clusteredBarChart',670,495,582,275,'customers','region','Contribution','Regional contribution')
    page(second,'Discount and return diagnosis');text(second,'title','Discount and return diagnosis','Synthetic data · Tier comparisons are descriptive, not causal estimates · Select a category to inspect its tiers')
    for i,m in enumerate(['Gross sales','Discounts','Refunds','Contribution','Orders']):card(second,i,m)
    chart(second,'discount','clusteredColumnChart',28,230,622,245,'orders','discount_band','Contribution margin','Margin by discount tier',('products','category'))
    chart(second,'returns','clusteredBarChart',670,230,320,245,'products','category','Unit return rate','Unit return rate');slicer(second,'orders','year')
    chart(second,'channels','clusteredBarChart',28,495,622,275,'orders','channel','Contribution','Contribution by sales channel')
    chart(second,'volume','clusteredBarChart',670,495,582,275,'products','category','Orders','Order volume: check the denominators')
else:
    page(first,'Service performance');text(first,'title','Customer support | SLA performance','Synthetic 2025 tickets · Snapshot: 01 Jan 2026 UTC · Calendar-hour SLAs · Pending tickets past deadline count as breaches')
    for i,m in enumerate(['Tickets','Response SLA','Resolution SLA','Open tickets','Overdue open']):card(first,i,m)
    chart(first,'trend','lineChart',28,230,622,245,'tickets','month','Response SLA','Response attainment by opening month')
    chart(first,'teams','clusteredBarChart',670,230,320,245,'teams','team','Response SLA','Team response attainment');slicer(first,'tickets','priority')
    chart(first,'priority','clusteredColumnChart',28,495,622,275,'teams','team','Response SLA','Compare within priority',('tickets','priority'))
    chart(first,'demand','clusteredColumnChart',670,495,582,275,'tickets','month','Tickets','Incoming ticket volume')
    page(second,'Backlog and survey coverage');text(second,'title','Backlog and survey coverage','Synthetic study · CSAT describes respondents only · Open-ticket age is measured at the snapshot, not today')
    for i,m in enumerate(['Open tickets','Overdue open','Survey responses','Positive CSAT','Response eligible']):card(second,i,m)
    chart(second,'aged','columnChart',28,230,622,245,'tickets','age_band','Open tickets','Open workload by age',('teams','team'))
    chart(second,'overdue','clusteredBarChart',670,230,320,245,'teams','team','Overdue open','Overdue open tickets');slicer(second,'tickets','priority')
    chart(second,'survey','clusteredBarChart',28,495,622,275,'teams','team','Survey responses','Survey response counts')
    chart(second,'csat','clusteredBarChart',670,495,582,275,'teams','team','Positive CSAT','Positive CSAT among respondents')
print(NAME+': model, measures, Power Query and two report pages written.')

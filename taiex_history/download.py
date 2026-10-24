import argparse,csv,json,time,random,pathlib,datetime,requests
p=argparse.ArgumentParser()
p.add_argument('--start',default='1990-01')
p.add_argument('--end',default='2026-10')
p.add_argument('--delay',type=float,default=2)
a=p.parse_args()
root=pathlib.Path('taiex_history');root.mkdir(exist_ok=True)
cache=root/'cache';cache.mkdir(exist_ok=True)
def months(s,e):
 y,m=map(int,s.split('-'));ey,em=map(int,e.split('-'))
 while (y,m)<=(ey,em):
  yield y,m
  m+=1
  if m==13:y,m=y+1,1
def normalize(rows):
 for r in rows:
  try:
   y,m,d=map(int,r[0].strip().split('/'))
   if y<1911:y+=1911
   date=datetime.date(y,m,d).isoformat()
   nums=[float(str(v).replace(',','')) for v in r[1:5]]
   if len(nums)==4:yield [date,*nums]
  except (ValueError,TypeError,IndexError):continue
allrows={};failed=[];success=[]
for y,m in months(a.start,a.end):
 key=f'{y}{m:02d}01';path=cache/f'{key}.json';obj=None
 if path.exists():
  try:obj=json.loads(path.read_text(encoding='utf8'))
  except Exception:pass
 if not obj:
  for endpoint in ['https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST','https://www.twse.com.tw/indicesReport/MI_5MINS_HIST']:
   for attempt in range(3):
    try:
     r=requests.get(endpoint,params={'date':key,'response':'json'},timeout=30,headers={'User-Agent':'Mozilla/5.0'})
     r.raise_for_status();candidate=r.json()
     if candidate.get('stat')=='OK' and candidate.get('data'):
      obj=candidate;path.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf8');break
    except Exception as e:print(key,str(e)[:100],flush=True)
    time.sleep(min(10,2**attempt+random.random()))
   if obj:break
  time.sleep(a.delay)
 if obj:
  success.append(key)
  for row in normalize(obj.get('data',[])):allrows[row[0]]=row
 else:failed.append(key)
with (root/'TAIEX_daily_merged.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['date','open','high','low','close']);w.writerows(allrows[k] for k in sorted(allrows))
(root/'download_status.json').write_text(json.dumps({'start':a.start,'end':a.end,'successful_months':len(success),'failed_months':failed,'daily_rows':len(allrows)},ensure_ascii=False,indent=2),encoding='utf8')
print('SUCCESS MONTHS',len(success),'FAILED MONTHS',len(failed),'ROWS',len(allrows),flush=True)

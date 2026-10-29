"""Bounded, complete JSON paging for the summarizing Codex session."""
import argparse,hashlib,json,math
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('messages');p.add_argument('--page',type=int);p.add_argument('--page-size',type=int,default=12000);a=p.parse_args()
 if not 100<=a.page_size<=12000:p.error('page-size must be 100..12000')
 raw=Path(a.messages).read_bytes();data=json.loads(raw.decode('utf-8-sig'));messages=data['messages'];meta=data['metadata']
 if meta['count']!=len(messages) or len({m['id'] for m in messages})!=len(messages):raise ValueError('message count or IDs inconsistent')
 text=json.dumps(data,ensure_ascii=False,indent=2);pages=max(1,math.ceil(len(text)/a.page_size))
 print(json.dumps({'sha256':hashlib.sha256(raw).hexdigest(),'messages':len(messages),'pages':pages,'page_size':a.page_size,'page':a.page},ensure_ascii=False))
 if a.page is not None:
  if not 1<=a.page<=pages:p.error('page out of range')
  print(text[(a.page-1)*a.page_size:a.page*a.page_size]);print(f'END PAGE {a.page}/{pages}')
if __name__=='__main__':main()

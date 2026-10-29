import argparse, collections, datetime as dt, hashlib, hmac, json, os, re, shutil, sqlite3, struct, sys, tempfile, time
from pathlib import Path
from contextlib import closing
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
TZ=dt.timezone(dt.timedelta(hours=8)); ROOT=Path(__file__).parent

def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),'utf-8')
def checksum(data, state=(0,0), endian='<'):
    a,b=state
    for x,y in struct.iter_unpack(endian+'II',data): a=(a+x+b)&0xffffffff; b=(b+y+a)&0xffffffff
    return a,b

def decrypt(src,out,key):
    from wechat_cli.core.crypto import decrypt_page
    raw=src.read_bytes(); salt=raw[:16]; mac=hashlib.pbkdf2_hmac('sha512',key,bytes(x^58 for x in salt),2,32)
    def page(data,n):
        start=16 if n==1 else 0
        if len(data)!=4096 or not hmac.compare_digest(hmac.new(mac,data[start:-64]+struct.pack('<I',n),'sha512').digest(),data[-64:]): raise ValueError(f'页 HMAC 校验失败: {src.name} page={n}')
        return decrypt_page(key,data,n)
    if len(raw)%4096: raise ValueError('数据库不是完整页')
    with out.open('wb') as f:
        for i in range(len(raw)//4096): f.write(page(raw[i*4096:(i+1)*4096],i+1))
    wal=Path(str(src)+'-wal'); count=0
    if wal.exists() and wal.stat().st_size:
        w=wal.read_bytes(); magic,version,psz=struct.unpack('>III',w[:12]); assert magic in (0x377f0682,0x377f0683) and psz==4096
        endian='<' if magic==0x377f0682 else '>'; state=checksum(w[:24],endian=endian)
        assert state==struct.unpack('>II',w[24:32]), 'WAL header checksum'
        pending=[]; committed=[]; size=None
        for pos in range(32,len(w)-4119,4120):
            fh=w[pos:pos+24]; data=w[pos+24:pos+4120]
            if fh[8:16]!=w[16:24]: break
            state=checksum(fh[:8]+data,state,endian)
            if state!=struct.unpack('>II',fh[16:24]): break
            n,dbsize=struct.unpack('>II',fh[:8]); assert n>0
            pending.append((n,data))
            if dbsize: committed.extend(pending); pending=[]; size=dbsize
        with out.open('r+b') as f:
            for n,data in committed: f.seek((n-1)*4096);f.write(page(data,n));count+=1
            if size: f.truncate(size*4096)
    with closing(sqlite3.connect(out)) as c: assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
    return count

def snapshot(src,dest):
    paths=[src,Path(str(src)+'-wal')]
    for attempt in range(4):
        before=[p.read_bytes() if p.exists() else None for p in paths]
        after=[p.read_bytes() if p.exists() else None for p in paths]
        if before==after:
            dest.parent.mkdir(parents=True,exist_ok=True)
            for i,data in enumerate(before):
                target=dest if i==0 else Path(str(dest)+'-wal')
                if data is not None: target.write_bytes(data)
            return
    raise RuntimeError('数据库持续变化，无法获取经验证的一致副本；请稍后重试')

def parse(content,typ):
    from wechat_cli.core.messages import _parse_xml_root,format_msg_type
    result={'type':format_msg_type(typ),'text':content,'card':None,'quote':None}
    if (typ & 0xffffffff) in (3,34,43,47): result['text']='['+result['type']+'，未解析媒体内容]'
    root=_parse_xml_root(content)
    if root is not None:
        template=root.find('.//template')
        if template is not None and template.text:
            text=template.text
            for link in root.findall('.//link'):
                text=text.replace('$'+str(link.get('name'))+'$', '、'.join(n.text or '' for n in link.findall('.//nickname')))
            result['text']=text
        app=root.find('.//appmsg')
        if app is not None:
            result['card']={k:app.findtext(k) for k in ('title','des','url','type')};result['text']=app.findtext('title') or '[卡片]'
            ref=app.find('.//refermsg')
            if ref is not None: result['quote']={k:ref.findtext(k) for k in ('svrid','displayname','content','type')}
    return result

def export(args):
    from wechat_cli.keys import scanner_windows as scanner
    from wechat_cli.keys.common import collect_db_files
    from wechat_cli.core.messages import decompress_content
    for value in (args.start,args.end):
        if value and dt.datetime.fromisoformat(value).tzinfo is None: raise ValueError('起止时间必须明确时区，例如 +08:00')
    end=dt.datetime.fromisoformat(args.end).astimezone(TZ) if args.end else dt.datetime.now(TZ).replace(microsecond=0)
    start=dt.datetime.fromisoformat(args.start).astimezone(TZ) if args.start else end-dt.timedelta(hours=args.hours)
    assert start<end
    accounts=list((Path.home()/'Documents/xwechat_files').glob('*/db_storage'))
    if args.account: accounts=[x for x in accounts if x.parent.name==args.account]
    if len(accounts)!=1: raise RuntimeError('请用 --account 选择账号: '+str([x.parent.name for x in accounts]))
    base=accounts[0]; paths=[base/'contact/contact.db']+sorted((base/'message').glob('message_[0-9]*.db'))
    files,salts=collect_db_files(str(base));files=[x for x in files if Path(x[1]) in paths];salts={s:[x[0] for x in files if x[3]==s] for s in {x[3] for x in files}}
    scanner.collect_db_files=lambda _: (files,salts)
    scanner.save_results=lambda db,sa,keys,*_: keys
    print('只读扫描并验证所需数据库密钥（不保存、不输出密钥）',flush=True)
    keys=scanner.extract_keys(str(base),None)
    if set(salts)-set(keys): raise RuntimeError('必要数据库密钥未全部验证，停止读取')
    result=[]; provenance=[]; group=None; names={}
    with tempfile.TemporaryDirectory(prefix='wechat-summary-') as tmp:
        tmp=Path(tmp)
        for src in paths:
            snap=tmp/('enc-'+src.name); plain=tmp/src.name;snapshot(src,snap)
            salt=snap.read_bytes()[:16].hex(); wal=decrypt(snap,plain,bytes.fromhex(keys[salt]));provenance.append({'database':src.name,'wal_committed_frames':wal})
            with closing(sqlite3.connect(plain)) as c:
                c.row_factory=sqlite3.Row
                if src.name=='contact.db':
                    rows=c.execute('select username,nick_name,remark from contact').fetchall();names={r['username']:r['remark'] or r['nick_name'] or r['username'] for r in rows}
                    matches=[dict(r) for r in rows if r['username'].endswith('@chatroom') and args.group in (r['nick_name'],r['remark']) and (not args.group_id or r['username']==args.group_id)]
                    if len(matches)!=1: raise RuntimeError('完整群名需消歧，请用 --group-id: '+json.dumps(matches,ensure_ascii=False))
                    group=matches[0]; print('匹配群: '+json.dumps(group,ensure_ascii=False),flush=True)
                else:
                    table='Msg_'+hashlib.md5(group['username'].encode()).hexdigest()
                    if not c.execute('select 1 from sqlite_master where name=?',(table,)).fetchone(): continue
                    columns=[r[1] for r in c.execute(f'pragma table_info([{table}])')]
                    required={'local_id','local_type','create_time','real_sender_id','message_content','WCDB_CT_message_content'}
                    if not required.issubset(columns): raise RuntimeError('不兼容的消息表字段')
                    mapping={r[0]:r[1] for r in c.execute('select rowid,user_name from Name2Id')}
                    # Unit validated against actual timestamp magnitude, never inferred from machine locale.
                    mx=c.execute(f'select max(create_time) from [{table}]').fetchone()[0] or 0
                    scale=1000 if mx>100000000000 else 1
                    q=c.execute(f'select * from [{table}] where create_time>=? and create_time<? order by create_time,local_id',(start.timestamp()*scale,end.timestamp()*scale))
                    for r in q:
                        content=decompress_content(r['message_content'],r['WCDB_CT_message_content'])
                        if content is None: raise RuntimeError('消息解压失败，停止而非忽略消息')
                        content=content or '';sender=mapping.get(r['real_sender_id'],str(r['real_sender_id']))
                        if ':\n' in content and content.split(':\n',1)[0] in names: sender,content=content.split(':\n',1)
                        sid=str(r['server_id']) if 'server_id' in columns else ''
                        mid='s'+sid if sid not in ('','0') else src.stem+'-'+str(r['local_id'])
                        result.append(dict(id=mid,local_id=r['local_id'],server_id=sid,timestamp=r['create_time']/scale,time=dt.datetime.fromtimestamp(r['create_time']/scale,TZ).isoformat(),sender_id=sender,sender=names.get(sender,sender),raw_content=content,database=src.name,**parse(content,r['local_type'])))
            plain.unlink()
    keys.clear(); unique={};duplicates=0
    for m in result:
        if m['id'] in unique:
            if {k:v for k,v in m.items() if k not in ('database','local_id')}!={k:v for k,v in unique[m['id']].items() if k not in ('database','local_id')}: raise RuntimeError('重复 ID 内容冲突')
            duplicates+=1
        unique[m['id']]=m
    result=sorted(unique.values(),key=lambda x:(x['timestamp'],x['id']))
    meta=dict(group=args.group,group_id=group['username'],account=base.parent.name,start=start.isoformat(),end=end.isoformat(),timezone='Asia/Shanghai UTC+08:00',interval='[start,end)',count=len(result),speakers=len({m['sender_id'] for m in result if m['type'] not in ('系统','撤回')}),system_count=sum(m['type'] in ('系统','撤回') for m in result),duplicates_removed=duplicates,databases=provenance,scope='仅本机已同步记录；无法证明该窗口与群完整历史一致。图片、视频、语音、表情未解析内容。')
    out=Path(args.output_root).resolve()/(end.strftime('%Y%m%d-%H%M%S')+'-'+str(time.time_ns())[-6:]);out.mkdir(parents=True,exist_ok=False);dump(out/'messages.json',dict(metadata=meta,messages=result))
    (out/'messages.txt').write_text('\n\n'.join(f"[{m['id']}] {m['time']} {m['sender']} ({m['type']})\n{m['text']}"+ ('\n引用:'+json.dumps(m['quote'],ensure_ascii=False) if m['quote'] else '') for m in result),'utf-8');print(out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-root',default=str(Path.cwd()/'wechat-reports'));p.add_argument('--group');p.add_argument('--group-id');p.add_argument('--account');p.add_argument('--hours',type=int,choices=[24,48,72],default=24);p.add_argument('--start');p.add_argument('--end');a=p.parse_args();a.group=a.group or input('完整群名: ');export(a)

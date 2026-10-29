import html,json,sys,math,base64
from pathlib import Path
from playwright.sync_api import sync_playwright

def render(folder):
    folder=Path(folder).resolve();data=json.loads((folder/'messages.json').read_text('utf-8-sig'));r=json.loads((folder/'report.json').read_text('utf-8-sig'));meta=data['metadata'];msgs={m['id']:m for m in data['messages']}
    assert meta['count']==len(msgs)
    esc=lambda x:html.escape(str(x),quote=True)
    md=[f"# {meta['group']}\n",f"{meta['start']} 至 {meta['end']}（Asia/Shanghai，包含起点、不包含终点）\n",f"消息 {meta['count']} 条 · 发言 {meta['speakers']} 人\n",meta['scope'], '\n## 简短概览\n'+r['overview']]
    body=f"<h1>{esc(meta['group'])}</h1><p>{esc(meta['start'])} 至 {esc(meta['end'])}</p><p>Asia/Shanghai · [起点, 终点)</p><p class='stat'>{meta['count']} 条消息 · {meta['speakers']} 位发言人</p><p>{esc(meta['scope'])}</p><h2>简短概览</h2><p>{esc(r['overview'])}</p>"
    for key,label in [('topics','主要话题及讨论结论'),('todos','待办事项'),('confirmed','已解决或已确认事项'),('unresolved','尚未解决的问题'),('other','其他信息')]:
        body+='<h2>'+label+'</h2>';md+=['\n## '+label]
        for item in r.get(key,[]):
            refs=item.get('refs',[]);assert refs and all(x in msgs for x in refs),'无效或缺失引用'
            text=item['text']
            if key=='todos': text+='；负责人：'+item.get('owner','未明确')+'；时间要求：'+item.get('deadline','未明确')+'；状态：'+item.get('status','未明确')
            md+=['- '+text+' ['+', '.join(refs)+']'];body+='<article><p>'+esc(text)+'</p><details><summary>核对来源（'+str(len(refs))+' 条）</summary>'
            for ref in refs:
                m=msgs[ref];body+=f"<blockquote><b>{esc(ref)} · {esc(m['time'])} · {esc(m['sender'])}</b><pre>{esc(m['text'])}</pre></blockquote>"
            body+='</details></article>'
        if not r.get(key): body+='<p>未发现明确记录。</p>';md+=['未发现明确记录。']
    body+='<footer>总结由当前 Codex 会话阅读全部导出消息后编写。群内陈述未经外部事实核实；媒体内容未解析。</footer>'
    css='*{box-sizing:border-box}body{margin:0;background:#edf2f5;color:#223246;font-family:"Microsoft YaHei",sans-serif;line-height:1.85}main{max-width:900px;margin:24px auto;background:white;padding:40px;border-radius:16px}h1{font-size:28px}h2{font-size:21px;border-bottom:2px solid #13a186;padding-bottom:8px;margin-top:28px}article{padding:12px 18px;margin:12px 0;background:#f5f8fa;border-radius:10px}p{overflow-wrap:anywhere;margin:8px 0}.stat{font-size:22px;color:#087d6b}summary{cursor:pointer;color:#087d6b}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}blockquote{margin:12px 0;padding:10px;border-left:3px solid #12a388}footer{font-size:13px;color:#64748b;margin-top:30px}@media(max-width:600px){main{padding:20px;margin:0;border-radius:0}h1{font-size:23px}}'
    (folder/'summary.md').write_text('\n'.join(md),'utf-8');(folder/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(meta['group'])+'</title><style>'+css+'</style><main>'+body+'</main></html>','utf-8')
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',headless=True)
        page=browser.new_page(viewport={'width':960,'height':800},device_scale_factor=1.5);page.goto((folder/'index.html').as_uri());page.evaluate('document.fonts.ready');height=page.evaluate('document.documentElement.scrollHeight');parts=math.ceil(height/12000)
        files=[]
        for i in range(parts):
            name='report.png' if i==0 else f'report-{i+1:02}.png';(folder/name).write_bytes(base64.b64decode(page.context.new_cdp_session(page).send('Page.captureScreenshot',{'format':'png','captureBeyondViewport':True,'clip':{'x':0,'y':i*12000,'width':960,'height':min(12000,height-i*12000),'scale':1}})['data']));files.append(name)
        page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth')==390
        browser.close();(folder/'render-check.json').write_text(json.dumps({'height':height,'png_files':files,'split_reason':'超过12000 CSS像素分图' if parts>1 else None,'mobile_overflow':False}),'utf-8')
    print(folder/'index.html')
if __name__=='__main__':render(sys.argv[1])


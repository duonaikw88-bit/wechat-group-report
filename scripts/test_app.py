import tempfile,unittest,json,shutil
from pathlib import Path
import app
class Tests(unittest.TestCase):
 def test_parse(self):
  x=app.parse('<msg><appmsg><title>&lt;script&gt;链接</title><type>57</type><refermsg><svrid>123</svrid><content>同意建议</content></refermsg></appmsg></msg>',49)
  self.assertEqual(x['quote']['svrid'],'123');self.assertEqual(x['text'],'<script>链接')
  self.assertIn('未解析',app.parse('secret',3)['text'])
 def test_snapshot_cleanup(self):
  with tempfile.TemporaryDirectory(prefix='wechat-summary-test-') as d:
   src=Path(d)/'source';src.write_bytes(b'123');app.snapshot(src,Path(d)/'copy');self.assertEqual(src.read_bytes(),b'123')
  self.assertFalse(Path(d).exists())
 def test_demo(self):
  from render import render
  p=Path('outputs/demo');p.mkdir(parents=True,exist_ok=True)
  msgs=[dict(id='demo1',time='2026-10-29T09:00:00+08:00',sender='小明<script>',sender_id='a',text='建议明天检查导出结果，尚未决定。',type='文本'),dict(id='demo2',time='2026-10-29T09:01:00+08:00',sender='小李',sender_id='b',text='收到。',type='文本')]
  app.dump(p/'messages.json',dict(metadata=dict(group='虚构测试群 <安全转义>',start='2026-10-28T10:00:00+08:00',end='2026-10-29T10:00:00+08:00',count=2,speakers=2,scope='虚构数据，不能证明真实微信读取成功。'),messages=msgs));(p/'messages.txt').write_text(str(msgs),'utf-8')
  app.dump(p/'report.json',dict(overview='成员提出检查导出的建议，对方回复收到；尚无明确决定或执行记录。',topics=[dict(text='提出检查导出结果的建议；收到不代表同意。',refs=['demo1','demo2'])],todos=[dict(text='建议检查导出结果',owner='未明确',deadline='建议明天，未确认',status='建议，未决定',refs=['demo1'])],confirmed=[],unresolved=[],other=[]));render(p)
  self.assertIn('&lt;安全转义&gt;',(p/'index.html').read_text('utf-8'));self.assertTrue((p/'report.png').exists())
if __name__=='__main__':unittest.main()

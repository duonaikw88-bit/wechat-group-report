import unittest,tempfile,sqlite3,json
from pathlib import Path
import app
class Invariants(unittest.TestCase):
 def test_time_boundary_and_full_cursor(self):
  with sqlite3.connect(':memory:') as c:
   c.execute('create table messages(id integer,create_time integer)');c.executemany('insert into messages values (?,?)',[(i,i) for i in range(1202)])
   rows=list(c.execute('select * from messages where create_time>=? and create_time<? order by create_time,id',(1,1201)))
   self.assertEqual(len(rows),1200);self.assertEqual(rows[0][0],1);self.assertEqual(rows[-1][0],1200)
 def test_bad_page_fail_closed_and_cleanup(self):
  with tempfile.TemporaryDirectory(prefix='wechat-summary-test-') as d:
   p=Path(d);(p/'enc').write_bytes(bytes(4096))
   with self.assertRaises(ValueError):app.decrypt(p/'enc',p/'plain',bytes(32))
  self.assertFalse(p.exists())
 def test_nonexistent_reference_rejected(self):
  from render import render
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);app.dump(p/'messages.json',{'metadata':{'count':0,'group':'x','start':'a','end':'b','speakers':0,'scope':'test'},'messages':[]});app.dump(p/'report.json',{'overview':'test','topics':[{'text':'bad','refs':['missing']}]})
   with self.assertRaises(AssertionError):render(p)
if __name__=='__main__':unittest.main()

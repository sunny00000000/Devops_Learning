import importlib.util, os, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ClassificationAuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();os.environ['BILLINGER_DB_PATH']=str(Path(cls.tmp.name)/'audit.db')
  spec=importlib.util.spec_from_file_location('audit_app',ROOT/'app.py');cls.app=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.app);cls.app.v2.DB_PATH=Path(os.environ['BILLINGER_DB_PATH']);cls.app.init_db()
 @classmethod
 def tearDownClass(cls): cls.tmp.cleanup();os.environ.pop('BILLINGER_DB_PATH',None)
 def test_every_tool_book_has_exactly_one_primary_placement(self):
  books=[r for r in self.app.RESOURCE_INDEX['resources'] if r.get('placement')=='tool']
  self.assertEqual(len(books),65)
  for r in books:
   self.assertEqual(r['tools'],[r['primary_tool']])
   self.assertIn(r['primary_tool'],self.app.TOOL_MAP)
 def test_program_guides_are_not_in_tool_lists(self):
  guides=[r for r in self.app.RESOURCE_INDEX['resources'] if r.get('placement')=='program']
  self.assertEqual(len(guides),4)
  self.assertTrue(all(not r['tools'] and not r['primary_tool'] for r in guides))
 def test_reported_mixing_examples_are_fixed(self):
  self.assertNotIn('vol-9c',{r['id'] for r in self.app.list_learning_resources('linux')['resources']})
  self.assertNotIn('vol-10a',{r['id'] for r in self.app.list_learning_resources('git')['resources']})
  self.assertEqual({r['id'] for r in self.app.list_learning_resources('ansible')['resources']},{'vol-9c','vol-9d'})
if __name__=='__main__': unittest.main(verbosity=2)

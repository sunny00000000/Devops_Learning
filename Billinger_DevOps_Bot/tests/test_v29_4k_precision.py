from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class Precision4KTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/'static/index.html').read_text(encoding='utf-8')
        cls.css=(ROOT/'static/styles.css').read_text(encoding='utf-8')
    def test_build_identity(self):
        self.assertIn('4K precision build 2.9.0',self.html)
        self.assertIn('/styles.css?v=2.9.0-4k',self.html)
        self.assertIn('/app.js?v=2.9.0-4k',self.html)
    def test_precision_css(self):
        for token in ['BILLINGER v2.9 4K PRECISION POLISH','backdrop-filter:none!important','max-width:2860px','@media (min-width:3400px)','--precision-surface:#0e151d']:
            self.assertIn(token,self.css)
    def test_no_blur_on_primary_precision_surfaces(self):
        self.assertIn('body.studio-experience .topbar,',self.css)
        self.assertIn('body.studio-experience .panel,',self.css)
        self.assertIn('-webkit-backdrop-filter:none!important',self.css)
if __name__=='__main__': unittest.main()

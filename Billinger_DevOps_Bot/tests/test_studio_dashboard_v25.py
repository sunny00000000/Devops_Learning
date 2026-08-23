from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class StudioDashboardV25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/'static/index.html').read_text(encoding='utf-8')
        cls.css=(ROOT/'static/styles.css').read_text(encoding='utf-8')
        cls.js=(ROOT/'static/app.js').read_text(encoding='utf-8')

    def test_original_offline_studio_assets_are_connected(self):
        # v2.5.1 intentionally uses one bundled, cache-busted stylesheet so a
        # missing secondary CSS file cannot expose the legacy dashboard.
        self.assertIn('href="/styles.css?v=2.9.0-4k"',self.html)
        self.assertNotIn('href="/studio.css"',self.html)
        self.assertIn('BILLINGER VERIFIED STUDIO UI BUNDLE v2.5.1',self.css)
        self.assertIn('class="hero panel hero-v22 studio-room"',self.html)
        self.assertIn('id="menuClose"',self.html)
        self.assertIn('id="navScrim"',self.html)
        self.assertIn('id="scrollProgress"',self.html)
        self.assertIn('4K precision build 2.9.0',self.html)
        self.assertNotRegex(self.html,r'<(?:script|link)[^>]+https?://')

    def test_navigation_and_accessibility(self):
        self.assertRegex(self.css,r'\.sidebar\{[^}]*overflow-y:auto')
        self.assertIn('@media(prefers-reduced-motion:reduce)',self.css)
        self.assertIn("$('#menuButton')?.setAttribute('aria-expanded','false')",self.js)
        self.assertIn('function closeStudioNav()',self.js)
        self.assertIn('id="billinger-studio-critical"',self.html)

    def test_html_ids_remain_unique(self):
        ids=re.findall(r'\bid="([^"]+)"',self.html)
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreater(len(ids),300)

    def test_lightweight_visual_layer(self):
        self.assertLess((ROOT/'static/styles.css').stat().st_size,160_000)
        self.assertNotIn('WebGL',self.js)
        self.assertNotIn('three.js',self.html.lower())
        self.assertNotIn('eval(',self.js)

if __name__=='__main__':
    unittest.main()

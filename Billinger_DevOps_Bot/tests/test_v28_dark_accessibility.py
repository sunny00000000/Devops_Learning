from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class DarkAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/'static/index.html').read_text(encoding='utf-8')
        cls.css=(ROOT/'static/styles.css').read_text(encoding='utf-8')
        cls.js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    def test_default_dark_high_contrast(self):
        self.assertIn('theme-comfort-dark high-contrast',self.html)
        self.assertIn('4K precision build 2.9.0',self.html)
        self.assertIn('meta name="theme-color" content="#080d13"',self.html)
    def test_controls_present(self):
        for id_ in ['displayTheme','displayTextSize','displayHighContrast','displayReduceMotion','comfortQuickToggle']:
            self.assertIn(f'id="{id_}"',self.html)
    def test_dark_css_and_persistence(self):
        for token in ['theme-comfort-dark','theme-standard-dark','high-contrast','reduce-motion','DISPLAY_PREF_KEY']:
            self.assertTrue(token in self.css or token in self.js)
        self.assertIn('localStorage.setItem(DISPLAY_PREF_KEY',self.js)
if __name__=='__main__': unittest.main()

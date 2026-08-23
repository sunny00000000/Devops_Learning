from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class VerifiedStudioV251Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/'static/index.html').read_text(encoding='utf-8')
        cls.css=(ROOT/'static/styles.css').read_text(encoding='utf-8')
        cls.app=(ROOT/'app.py').read_text(encoding='utf-8')

    def test_studio_is_bundled_and_cache_busted(self):
        self.assertIn('/styles.css?v=2.9.0-4k', self.html)
        self.assertNotIn('href="/studio.css"', self.html)
        self.assertIn('BILLINGER VERIFIED STUDIO UI BUNDLE v2.5.1', self.css)

    def test_legacy_sidebar_cannot_be_default_layout(self):
        self.assertIn('id="billinger-studio-critical"', self.html)
        self.assertIn('transform:translateX(-103%)', self.html)
        self.assertIn('.sidebar.open{transform:translateX(0)}', self.css)

    def test_build_is_visibly_identifiable(self):
        self.assertIn('4K precision build 2.9.0', self.html)
        self.assertIn('VERIFIED STUDIO INTERFACE', (ROOT/'UPDATE_NOTES_v2.5.1.txt').read_text(encoding='utf-8'))

    def test_old_running_server_does_not_mask_new_build(self):
        self.assertIn('for candidate_port in range(requested_port, requested_port + 20):', self.app)
        self.assertIn('port {requested_port} was already in use', self.app)

    def test_v262_four_provider_and_contrast_patch_is_bundled(self):
        self.assertIn('repeat(4,minmax(0,1fr))', self.css)
        self.assertIn('--studio-soft:#3b3732', self.css)
        self.assertIn('FOUR-PROVIDER + HIGH-CONTRAST', self.css)
        self.assertIn('4 online AI providers', self.html)


if __name__=='__main__':
    unittest.main()

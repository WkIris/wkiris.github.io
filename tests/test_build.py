import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_site import export_site

class ExportTests(unittest.TestCase):
    def test_only_referenced_assets_and_licenses_are_published(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);source=base/'source';source.mkdir();output=base/'dist'
            (source/'assets').mkdir();(source/'assets/vendor').mkdir()
            (source/'index.html').write_text('<link href="assets/style.css"><img src="assets/头像.jpg"><a href="https://example.com/">link</a>')
            (source/'assets/style.css').write_text('@import url("extra.css"); body { background: url("photo.png"); }')
            (source/'assets/extra.css').write_text('h1 {color: navy}')
            (source/'assets/photo.png').write_bytes(b'photo');(source/'assets/头像.jpg').write_bytes(b'avatar')
            (source/'assets/vendor/font-LICENSE.txt').write_text('License')
            (source/'private.txt').write_text('not for publication')
            export_site(source,output)
            self.assertTrue((output/'assets/头像.jpg').exists())
            self.assertTrue((output/'assets/extra.css').exists())
            self.assertTrue((output/'assets/vendor/font-LICENSE.txt').exists())
            self.assertFalse((output/'private.txt').exists())
            self.assertTrue((output/'.nojekyll').exists())

    def test_missing_or_outside_asset_prevents_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);source=base/'source';source.mkdir()
            for url in ['missing.jpg','../outside.txt']:
                (source/'index.html').write_text(f'<img src="{url}">')
                with self.assertRaises(ValueError):export_site(source,base/'dist')

if __name__=='__main__':unittest.main()

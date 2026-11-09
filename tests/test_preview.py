import functools
import http.server
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from preview import Handler, ProfileWatcher

class PreviewTests(unittest.TestCase):
    def test_saved_text_updates_page_and_invalid_save_preserves_last_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / '个人信息.txt'
            output = root / 'index.html'
            profile.write_text('【基本信息】\n姓名：Before\n【个人介绍】\nOriginal bio')
            watcher = ProfileWatcher(profile, output, interval=0.025)
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=directory))
            server.profile_watcher = watcher
            threading.Thread(target=watcher.run, daemon=True).start()
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base = f'http://127.0.0.1:{server.server_port}'
            def read(path):
                with urlopen(base + path, timeout=2) as response:
                    return response.read().decode()
            def wait_for(predicate):
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    if predicate(): return
                    time.sleep(0.025)
                self.fail('Profile update timed out')
            try:
                original_version = json.loads(read('/__profile_version__'))['version']
                self.assertIn('Original bio', read('/'))
                self.assertIn("fetch('/__profile_version__'", read('/index.html'))
                profile.write_text('【基本信息】\n姓名：After\n【个人介绍】\nUpdated bio')
                wait_for(lambda: 'Updated bio' in read('/'))
                self.assertNotEqual(original_version, json.loads(read('/__profile_version__'))['version'])
                self.assertIn('<h1>After</h1>', output.read_text())
                self.assertNotIn('__profile_version__', output.read_text())
                profile.write_text('【基本信息】\n姓名：')
                wait_for(lambda: bool(json.loads(read('/__profile_version__'))['error']))
                self.assertIn('Updated bio', read('/'))
                profile.write_text('【基本信息】\n姓名：Recovered')
                wait_for(lambda: 'Recovered' in read('/'))
                self.assertFalse(json.loads(read('/__profile_version__'))['error'])
            finally:
                watcher.stop.set()
                server.shutdown()
                server.server_close()

if __name__ == '__main__': unittest.main()

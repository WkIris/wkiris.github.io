#!/usr/bin/env python3
"""Preview the author's HTML edition locally, without a Ruby installation."""
import argparse
import errno
import functools
import http.server
import hashlib
import json
import threading
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

from profile_page import PROFILE, OUTPUT, ProfileError, build_profile

ROOT = Path(__file__).resolve().parents[1] / "html_source_file"
MARKER = b"minimal-light-local-preview-v1"


class ProfileWatcher:
    def __init__(self, profile=PROFILE, output=OUTPUT, interval=1):
        self.profile, self.output, self.interval = profile, output, interval
        self.version = build_profile(profile, output)
        self.error = ''
        self.stop = threading.Event()

    def run(self):
        while not self.stop.wait(self.interval):
            try:
                digest = hashlib.sha256(self.profile.read_text(encoding='utf-8-sig').encode()).hexdigest()
                if digest != self.version:
                    self.version = build_profile(self.profile, self.output)
                    print('个人信息已保存，主页已更新。', flush=True)
                self.error = ''
            except (OSError, ProfileError) as error:
                message = str(error)
                if message != self.error:
                    print(f'个人信息未更新：{message}（保留上次正常页面）', flush=True)
                self.error = message


LIVE_SCRIPT = '''<script>
(() => {
  const version = __VERSION__;
  let pending = false;
  setInterval(async () => {
    if (pending) return;
    pending = true;
    try {
      const response = await fetch('/__profile_version__', {cache: 'no-store'});
      if (!response.ok) return;
      const state = await response.json();
      let notice = document.getElementById('profile-edit-notice');
      if (state.error) {
        if (!notice) {
          notice = document.createElement('div');
          notice.id = 'profile-edit-notice';
          notice.setAttribute('role', 'status');
          notice.style.cssText = 'position:fixed;bottom:12px;left:12px;right:12px;padding:12px;background:#fff3cd;color:#664d03;border:1px solid #ffecb5;border-radius:6px;z-index:9999;font:14px/1.5 sans-serif;';
          document.body.append(notice);
        }
        notice.textContent = '个人信息未更新：' + state.error + ' 已保留上次正常页面。';
      } else if (notice) notice.remove();
      if (state.version !== version) location.reload();
    } catch (_) { /* Keep the page usable if the local preview is stopped. */ }
    finally { pending = false; }
  }, 1000);
})();
</script>'''


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/__minimal_light_preview__":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(MARKER)
            return
        watcher = self.server.profile_watcher
        if path == '/__profile_version__':
            body = json.dumps({'version': watcher.version, 'error': watcher.error}, ensure_ascii=False).encode()
            self.send_body(body, 'application/json; charset=utf-8')
            return
        if path in {'/', '/index.html'}:
            # Inject refresh support only in the local preview, not in static exports.
            version = watcher.version
            body = watcher.output.read_text().replace('</body>', LIVE_SCRIPT.replace('__VERSION__', json.dumps(version)) + '</body>').encode()
            self.send_body(body, 'text/html; charset=utf-8')
            return
        super().do_GET()

    def send_body(self, body, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if urlsplit(self.path).path != '/__profile_version__':
            super().log_message(format, *args)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true", help="Open the browser")
    args = parser.parse_args()
    handler = functools.partial(Handler, directory=str(ROOT))
    for port in range(4000, 4011):
        url = f"http://127.0.0.1:{port}/"
        try:
            server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        except OSError as error:
            if error.errno != errno.EADDRINUSE:
                raise SystemExit(f"无法启动本地预览：{error}") from error
            try:
                with urllib.request.urlopen(url + "__minimal_light_preview__", timeout=1) as response:
                    if response.read() == MARKER:
                        print(f"主页已在运行：{url}", flush=True)
                        if args.open:
                            webbrowser.open(url)
                        return
            except (OSError, ValueError):
                pass
            continue
        print(f"本地主页：{url}\n保留此窗口即可继续访问，按 Ctrl+C 停止。", flush=True)
        try:
            watcher = ProfileWatcher()
        except (OSError, ProfileError) as error:
            server.server_close()
            raise SystemExit(f'请先检查个人信息.txt：{error}') from error
        server.profile_watcher = watcher
        threading.Thread(target=watcher.run, daemon=True).start()
        if args.open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n主页预览已停止。")
        finally:
            watcher.stop.set()
            server.server_close()
        return
    raise SystemExit("4000–4010 端口都已被占用，请关闭不用的预览后重试。")


if __name__ == "__main__":
    main()

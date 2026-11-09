"""Build a Pages artifact containing only files referenced by the homepage."""
import re
import shutil
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from profile_page import PROJECT, build_profile


def export_site(source, output):
    source = source.resolve()
    output = output.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('Export directory must be separate from source')
    files = set()
    pending = ['index.html']

    def add(url, referencing):
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return
        path = unquote(parsed.path)
        asset = (source / path.lstrip('/') if path.startswith('/') else (source / referencing).parent / path).resolve()
        if not asset.is_relative_to(source):
            raise ValueError(f'Asset is outside website: {url}')
        if not asset.is_file():
            raise ValueError(f'Missing asset: {asset.relative_to(source)}')
        relative = str(asset.relative_to(source))
        if relative not in files:
            pending.append(relative)

    class References(HTMLParser):
        def handle_starttag(self, tag, attributes):
            for name, value in attributes:
                if name in {'href', 'src'} and value:
                    add(value, 'index.html')

    while pending:
        relative = pending.pop()
        if relative in files:
            continue
        files.add(relative)
        path = source / relative
        if relative == 'index.html':
            References().feed(path.read_text(encoding='utf-8'))
        elif path.suffix == '.css':
            for url in re.findall(r'url\([\"\']?([^\)\"\']+)', path.read_text(encoding='utf-8')):
                add(url, relative)

    vendor = source / 'assets/vendor'
    if vendor.exists():
        for path in vendor.iterdir():
            if path.is_file() and 'LICENSE' in path.name:
                files.add(str(path.relative_to(source)))

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.homepage-build-', dir=output.parent) as directory:
        staging = Path(directory) / 'site'
        staging.mkdir()
        for relative in sorted(files):
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, destination)
        (staging / '.nojekyll').touch()
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
    return files


if __name__ == '__main__':
    build_profile()
    files = export_site(PROJECT / 'html_source_file', PROJECT / 'dist')
    print(f'Built {len(files)} website files in dist/.')

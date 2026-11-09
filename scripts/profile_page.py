"""Render a static homepage from a Chinese plain-text profile, using stdlib only."""
import hashlib
import html
import re
from pathlib import Path
from urllib.parse import urlsplit

PROJECT = Path(__file__).resolve().parents[1]
PROFILE = PROJECT / '个人信息.txt'
OUTPUT = PROJECT / 'html_source_file/index.html'
TEMPLATE = PROJECT / 'scripts/page-template.html'
FIELDS = {
    '基本信息': {'姓名', '身份', '单位', '单位网址', '邮箱', '头像', '简历', 'Google Scholar', 'GitHub', 'B站', 'LinkedIn', 'X', '网站描述', '网站域名'},
    '论文': {'标题', '作者', '发表信息', '会议简称', '图片', 'PDF', '代码', '项目主页', 'BibTex', '备注'},
    '项目': {'名称', '简介', '链接', '图片'},
}
TEXT_SECTIONS = {'个人介绍', '研究方向', '个人动态', '会议审稿', '期刊审稿'}


class ProfileError(ValueError):
    pass


def parse_profile(text):
    result = {name: [] for name in TEXT_SECTIONS}
    result.update({'基本信息': {}, '论文': [], '项目': []})
    section = None
    current = None
    last_key = None
    seen = set()
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue
        match = re.fullmatch(r'【(.+)】', stripped)
        if match:
            section = match.group(1)
            if section not in FIELDS and section not in TEXT_SECTIONS:
                raise ProfileError(f'第 {number} 行：不认识栏目“{section}”，请保留原来的栏目名称。')
            if section in seen and section not in {'论文', '项目'}:
                raise ProfileError(f'第 {number} 行：栏目“{section}”重复了。')
            seen.add(section)
            last_key = None
            if section in {'论文', '项目'}:
                current = {}
                result[section].append(current)
            elif section == '基本信息':
                current = result[section]
            continue
        if section is None:
            if stripped:
                raise ProfileError(f'第 {number} 行：请把内容写在【栏目名称】下面。')
            continue
        if section in TEXT_SECTIONS:
            result[section].append(line)
        elif stripped:
            if line[:1].isspace() and last_key:
                current[last_key] += '\n' + stripped
                continue
            pair = re.split(r'[：:]', stripped, maxsplit=1)
            if len(pair) != 2 or pair[0].strip() not in FIELDS[section]:
                raise ProfileError(f'第 {number} 行：请使用“字段名称：内容”的格式，字段名称需与示例一致。')
            key, value = pair[0].strip(), pair[1].strip()
            if key in current:
                raise ProfileError(f'第 {number} 行：“{key}”重复了。')
            current[key] = value
            last_key = key
    if not result['基本信息'].get('姓名'):
        raise ProfileError('请填写【基本信息】里的“姓名”。')
    for section, title in [('论文', '标题'), ('项目', '名称')]:
        result[section] = [item for item in result[section] if any(item.values())]
        for item in result[section]:
            if not item.get(title):
                raise ProfileError(f'【{section}】填写了内容，但缺少“{title}”。')
    return result


def esc(value):
    return html.escape(value, quote=True)


def safe_url(value):
    value = value.strip()
    if not value or any(c in value for c in '\r\n\t'):
        return ''
    try:
        parts = urlsplit(value)
    except ValueError:
        return ''
    if parts.scheme in {'https', 'http'} and parts.netloc:
        return esc(value)
    if not parts.scheme and not parts.netloc and not value.startswith(('/', '\\', '#')) and '..' not in parts.path.split('/') and '\\' not in value:
        return esc(value)
    return ''


def paragraphs(value):
    return ''.join('<p>' + '<br>'.join(esc(line.strip()) for line in block.splitlines()) + '</p>' for block in re.split(r'\n\s*\n', value.strip()) if block.strip())


def item_list(lines):
    items = []
    for line in lines:
        line = re.sub(r'^[-•]\s*', '', line.strip())
        if not line:
            continue
        items.append('<li>' + esc(line) + '</li>')
    return '<ul>' + ''.join(items) + '</ul>' if items else ''


def render_page(data):
    basic = data['基本信息']
    header = []
    avatar = safe_url(basic.get('头像', './assets/img/profile-photo.jpg'))
    if avatar:
        header.append(f'<a class="image avatar"><img src="{avatar}" alt="个人头像"></a>')
    header.append(f'<h1>{esc(basic["姓名"])}</h1>')
    if basic.get('身份'):
        header.append(f'<position style="font-size:1.10rem;">{esc(basic["身份"])}</position><br>')
    if basic.get('单位'):
        affiliation = '<autocolor>' + esc(basic['单位']) + '</autocolor>'
        url = safe_url(basic.get('单位网址', ''))
        header.append((f'<a href="{url}" rel="noopener">{affiliation}</a>' if url else affiliation) + '<br>')
    if basic.get('邮箱'):
        header.append('<email>' + esc(basic['邮箱']) + '</email>')
    socials = []
    for key, icon in [('Google Scholar', 'ai ai-google-scholar'), ('简历', 'ai ai-cv'), ('GitHub', 'fab fa-github'), ('B站', ''), ('LinkedIn', 'fab fa-linkedin'), ('X', 'fab fa-twitter')]:
        url = safe_url(basic.get(key, ''))
        if url:
            symbol = ('''<svg viewBox="0 0 24 24" width="21" height="21" style="vertical-align:-0.15em" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m8 3 2 3m6-3-2 3"/><rect x="3" y="7" width="18" height="14" rx="3"/><path d="M8 12v3m8-3v3m-6 3 2 1 2-1"/></svg>'''
                      if key == 'B站' else f'<i class="{icon}"></i>')
            socials.append(f'<a href="{url}" aria-label="{key}" title="{key}" rel="noopener">{symbol}</a>')
    if socials:
        header.append('<br><br><div class="social-icons">' + ''.join(socials) + '</div><br>')
    content = []
    def add(identifier, title, body):
        if body:
            content.append(f'<h2 id="{identifier}">{title}</h2>' + body)
    add('about-me', 'About Me', paragraphs('\n'.join(data['个人介绍'])))
    add('research-interests', 'Research Interests', item_list(data['研究方向']))
    add('news', 'News', item_list(data['个人动态']))
    publications = []
    for item in data['论文']:
        image = safe_url(item.get('图片', ''))
        row = '<li><div class="pub-row">'
        if image:
            row += f'<div class="col-sm-3 abbr" style="position:relative;padding:0 15px;"><img src="{image}" alt="{esc(item["标题"])}" class="teaser img-fluid z-depth-1">'
            if item.get('会议简称'):
                row += '<abbr class="badge">' + esc(item['会议简称']) + '</abbr>'
            row += '</div>'
        row += '<div class="col-sm-9" style="position:relative;padding:0 20px;">'
        title = esc(item['标题'])
        url = safe_url(item.get('PDF', '') or item.get('项目主页', ''))
        row += '<div class="title">' + (f'<a href="{url}">{title}</a>' if url else title) + '</div>'
        for key, cls in [('作者', 'author'), ('发表信息', 'periodical')]:
            if item.get(key):
                row += f'<div class="{cls}">{esc(item[key])}</div>'
        row += '<div class="links">'
        for key, label in [('PDF', 'PDF'), ('代码', 'Code'), ('项目主页', 'Project Page'), ('BibTex', 'BibTex')]:
            url = safe_url(item.get(key, ''))
            if url:
                row += f'<a href="{url}" class="btn btn-sm z-depth-0" target="_blank" rel="noopener" style="font-size:12px;">{label}</a> '
        if item.get('备注'):
            row += '<strong><i style="color:#e74d3c">' + esc(item['备注']) + '</i></strong>'
        row += '</div></div></div></li><br>'
        publications.append(row)
    add('publications', 'Publications', '<div class="publications"><ol class="bibliography">' + ''.join(publications) + '</ol></div>' if publications else '')
    projects = []
    for item in data['项目']:
        url = safe_url(item.get('链接', ''))
        title = esc(item['名称'])
        block = '<h3>' + (f'<a href="{url}">{title}</a>' if url else title) + '</h3>'
        image = safe_url(item.get('图片', ''))
        if image:
            block += f'<img src="{image}" alt="{title}" style="max-width:100%;border-radius:8px;">'
        block += paragraphs(item.get('简介', ''))
        projects.append(block)
    add('projects', 'Projects', ''.join(projects))
    services = []
    for key, title in [('会议审稿', 'Conference Reviewers'), ('期刊审稿', 'Journal Reviewers')]:
        listing = item_list(data[key])
        if listing:
            services.append('<h4>' + title + '</h4>' + listing)
    add('services', 'Services', ''.join(services))
    content.append('<br><p><small>Powered by <a href="https://github.com/yaoyao-liu/minimal-light" target="_blank" rel="noopener">Minimal Light</a> theme.</small></p>')
    title = basic['姓名'] + (' | ' + basic['单位'] if basic.get('单位') else '')
    canonical = safe_url(basic.get('网站域名', ''))
    return (TEMPLATE.read_text().replace('__PAGE_TITLE__', esc(title))
            .replace('__PAGE_DESCRIPTION__', esc(basic.get('网站描述', '')))
            .replace('__CANONICAL__', f'<link rel="canonical" href="{canonical}">' if canonical else '')
            .replace('__PROFILE_HEADER__', '\n'.join(header))
            .replace('__PROFILE_CONTENT__', '\n\n'.join(content)))


def build_profile(profile=PROFILE, output=OUTPUT):
    text = profile.read_text(encoding='utf-8-sig')
    page = render_page(parse_profile(text))
    # Replace atomically; a partially saved/invalid form never damages the last page.
    temporary = output.with_suffix('.html.tmp')
    temporary.write_text(page, encoding='utf-8')
    temporary.replace(output)
    return hashlib.sha256(text.encode()).hexdigest()


if __name__ == '__main__':
    try:
        build_profile()
        print('已根据个人信息.txt 更新主页。')
    except (ProfileError, OSError) as error:
        raise SystemExit(f'个人信息未更新：{error}')

import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from profile_page import parse_profile, render_page, ProfileError

class ProfileTests(unittest.TestCase):
    def test_bilibili_link_is_optional_and_safe(self):
        for value, visible in [('https://space.bilibili.com/123456', True), ('', False), ('javascript:alert(1)', False)]:
            page = render_page(parse_profile('【基本信息】\n姓名：Test\nB站：' + value))
            self.assertEqual('aria-label="B站"' in page, visible)
            if visible:
                self.assertIn('href="https://space.bilibili.com/123456"', page)
                self.assertIn('<svg', page)

    def test_chinese_text_and_multiline(self):
        page = render_page(parse_profile('【基本信息】\n姓名：王一钧\n单位: A & B\n\n【个人介绍】\n第一段：研究方向。\n继续介绍。\n\n第二段。\n\n【研究方向】\n机器学习\n计算机视觉\n'))
        self.assertIn('王一钧', page)
        self.assertIn('A &amp; B', page)
        self.assertIn('第一段：研究方向。<br>继续介绍。', page)
        self.assertIn('<p>第二段。</p>', page)
        self.assertIn('<li>机器学习</li>', page)
        self.assertNotIn('id="news"', page)
        self.assertNotIn('id="publications"', page)
        self.assertIn('profile-photo.jpg', page)

    def test_publications_projects_and_untrusted_text(self):
        text = '''【基本信息】
姓名：Test <script>alert(1)</script>
GitHub：javascript:alert(1)
【论文】
标题：论文 A
作者：A & B
发表信息：2026
PDF：https://example.com/paper.pdf
【论文】
标题：论文 B
【项目】
名称：Project
简介：第一行
    第二行
链接：https://example.com/
'''
        page = render_page(parse_profile(text))
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertNotIn('javascript:', page)
        self.assertIn('论文 A', page)
        self.assertIn('论文 B', page)
        self.assertIn('https://example.com/paper.pdf', page)
        self.assertIn('Project', page)
        self.assertIn('第二行', page)

    def test_errors_do_not_silently_drop_information(self):
        for text in ['【基本信息】\n姓名：\n', '【基本信心】\n姓名：Test', '【基本信息】\n姓名：Test\n未知字段：abc', '【论文】\n作者：Test']:
            with self.subTest(text=text), self.assertRaises(ProfileError):
                parse_profile(text)

if __name__ == '__main__':
    unittest.main()

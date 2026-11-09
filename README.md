# Yijun Wang 的个人主页

访问地址：**https://wkiris.github.io/**

## 更新个人信息

只需编辑 **[个人信息.txt](个人信息.txt)**，保留【栏目名称】和冒号前的字段名，修改后面的文字。空字段和空栏目会自动隐藏。增加论文或项目时，复制整段对应栏目并填写。

### 最方便：在 GitHub 网页上编辑

1. 打开 [个人信息.txt](https://github.com/WkIris/wkiris.github.io/edit/main/个人信息.txt)。
2. 修改并点击 Commit changes，提交到 main。
3. GitHub 会自动检查、生成和发布主页，通常需要几分钟。
4. 到 [Actions](https://github.com/WkIris/wkiris.github.io/actions) 查看结果。

填写出错或引用了不存在的图片时，发布会停止，线上保留上次成功版本。请根据 Actions 中的提示修正，再提交。

仓库和网站均公开。此文件只填写愿意公开的信息，不要上传密码、密钥或未公开的材料。

### 在本机编辑

双击 **打开个人主页.command** 启动预览。保存个人信息.txt 后，本地页面约 2 秒内自动刷新。

本地修改要提交并推送到 GitHub 后，线上才会更新；仅本地保存不会上传。

```sh
git pull --ff-only
# 编辑个人信息.txt 并保存
git add 个人信息.txt
git commit -m "Update personal profile"
git push
```

如果改过图片或样式，也需要一起提交对应文件。网页上修改过资料后，在本地继续编辑前先同步。

## 图片与链接

- 图片放在 html_source_file/assets/img/，填写文件中写 `assets/img/文件名`。
- 头像及裁切位置已保留，可通过“头像”字段更换文件。
- 简历文件可放入 html_source_file/assets/files/，再填写“简历”路径。
- GitHub、B站等链接填在相应字段中，留空则隐藏。

## 自动发布

每次向 main 提交修改，GitHub Actions 会运行测试，根据个人信息.txt 生成网页，并只发布网页实际引用的资源。

- 内容：个人信息.txt
- 页面模板：scripts/page-template.html
- 页面生成：scripts/profile_page.py
- 发布文件打包：scripts/build_site.py
- 发布流程：.github/workflows/pages.yml
- 本地预览：scripts/preview.py

无需安装第三方 Python 包、Ruby 或 Jekyll。生成的 index.html 和 dist/ 不提交到仓库。

手动检查：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
```

## 来源与许可

页面基于 [Minimal Light](https://github.com/yaoyao-liu/minimal-light)，保留原模板 CC0 许可。字体和图标的许可随资源保存在 assets/vendor/。个人照片及个人资料的权利属于本人，不因模板许可而改变。

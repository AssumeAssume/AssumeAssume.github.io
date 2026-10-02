# Xiufeng Li 学术网站

一个可部署到 GitHub Pages 的英文个人学术网站。页面内容来自本目录中的 CV，三个设计共用 `content/profile.json`。静态页面在构建时生成，访问者关闭 JavaScript 也可以阅读论文和履历。

发布地址：[assumeassume.github.io](https://assumeassume.github.io/)。源代码仓库：[AssumeAssume/AssumeAssume.github.io](https://github.com/AssumeAssume/AssumeAssume.github.io)。仓库的 `main` 分支更新后，GitHub Actions 会自动检查并部署网站。

## 查看设计

在本目录运行：

```sh
python3 scripts/build.py --include-previews
python3 scripts/serve.py --background
```

打开 <http://127.0.0.1:8787/preview/> 比较三种设计，也可以直接打开：

`--background` 让预览服务独立于当前聊天和终端运行。命令会显示进程 PID 与日志路径；需要关闭时可以使用 `kill <PID>`。如果希望在终端中前台运行，可省略 `--background`，使用 Ctrl+C 关闭。

| 选项 | 风格 | 本地页面 |
| --- | --- | --- |
| A | 经典学术，资料侧栏与紧凑论文列表 | <http://127.0.0.1:8787/preview/a/> |
| B | 极简现代，留白与期刊封面 | <http://127.0.0.1:8787/preview/b/> |
| C | 研究作品集，互动示意与论文特写，当前默认 | <http://127.0.0.1:8787/preview/c/> |

风格参考为 [Academic Pages](https://academicpages.github.io/)、[al-folio](https://alshedivat.github.io/al-folio/) 和 [Hugo Apéro](https://hugo-apero.netlify.app/)。这三个页面是自行实现的布局，没有安装这些主题。选择风格不会影响内容，也不需要切换技术框架。

当前采用 C：深色首页、衬线大标题、可切换的 LINE-1 / ANKRD11 / Regulatory AI 概念示意，以及独立的 Trends in Genetics 封面特写。示意图用于解释研究主题，不表示实验测量结果；标签支持鼠标、触屏及方向键切换。

## 更新内容

修改 `content/profile.json`，然后重新构建：

- `theme`：使用 `classic`、`minimal` 或 `editorial`。
- `intro`、`about`、`direction`：介绍和研究方向。
- `research`、`publications`、`news`：研究、论文和动态。
- `positions`、`education` 等：履历。
- `links`：学术账号与联系链接。
- `site_url`：上线后的完整网址，留空时不会生成未经确认的网址。填写后自动生成 canonical 和 sitemap。

```sh
python3 scripts/build.py --include-previews
python3 scripts/check.py
```

也可以临时指定风格：`python3 scripts/build.py --theme editorial --include-previews`。正式部署读取配置文件中的 `theme`。

## 部署到 GitHub Pages

1. 将网站源文件放入目标仓库的 `main` 分支。个人主页通常使用 `<username>.github.io` 作为仓库名，也支持普通项目仓库。
2. 在 GitHub 仓库的 **Settings → Pages → Build and deployment → Source** 中选择 **GitHub Actions**。
3. 推送代码，或手动运行 **Actions → Deploy academic website to GitHub Pages → Run workflow**。部署完成后的网址在工作流结果和 Pages 设置中显示。

`.github/workflows/pages.yml` 已包含构建、内部链接检查和部署步骤。正式部署不包含设计比较页面。资源与内部链接使用相对路径，同时支持 `https://username.github.io/` 和 `https://username.github.io/repository/`。

原始的 `CV_from_MSCA.docx`、`CV_from_MSCA.pdf` 已加入 `.gitignore`，且不会复制到公开网站。网站的 `/cv/` 是从公开内容配置生成的独立履历，可以通过 **Print / Save PDF** 保存。只有 `_site/` 中的构建结果会部署。

只需要 Python 3.9 或更新版本；没有 npm、Ruby 或第三方 Python 包依赖。`_site/` 是自动生成的目录，请修改源文件而非其中的 HTML。

GitHub 官方说明：[创建 Pages 网站](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)、[使用自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 内容来源

职业与教育经历、研究总结、论文作者和 DOI、奖项、教学与服务来自 `CV_from_MSCA.docx`。当前身份使用 CV 中的 2026 年 9 月起 VIB 博士后职位。Nature Genetics 论文的卷页与代码链接核对了[期刊原文](https://www.nature.com/articles/s41588-024-01789-5)。GitHub 账号链接来自该论文的代码仓库。

Trends in Genetics 封面图从 CV 中原样提取，页面已标注 Cell Press；它不属于本项目原创设计。其他页面布局与代码在本项目中创建。Molecular Cell 论文在 CV 中没有 DOI，因此目前保留标题与 BibTeX，不添加猜测的论文链接。

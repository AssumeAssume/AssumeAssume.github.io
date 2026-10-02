#!/usr/bin/env python3
"""Build an academic website with Python's standard library."""
import argparse
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
THEMES = {"classic": "a", "minimal": "b", "editorial": "c"}


def esc(value):
    return html.escape(str(value), quote=True)


def external(url, label, css=""):
    if urlsplit(url).scheme not in {"https", "http"}:
        raise ValueError(f"Unsupported URL: {url}")
    return f'<a class="{esc(css)}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'


def socials(profile, css="social-links"):
    return f'<div class="{css}">' + "".join(external(item["url"], esc(item["label"])) for item in profile["links"]) + "</div>"


def head(profile, prefix, title=None, lang="en", canonical="", robots="", styles=()):
    description = profile["description"]
    metadata = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    if robots:
        metadata += f'<meta name="robots" content="{esc(robots)}">'
    extra_styles = ''.join(f'<link rel="stylesheet" href="{prefix}assets/{esc(style)}">' for style in styles)
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title or profile['name'] + ' | Regulatory Genomics')}</title>
<meta name="description" content="{esc(description)}"><meta name="theme-color" content="#183f3a">
<meta property="og:title" content="{esc(title or profile['name'])}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website">
{metadata}<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/site.css">{extra_styles}</head>'''


def header(profile, prefix="", home=""):
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="header-inner">
<a class="brand" href="{home or '#about'}">{esc(profile['name'])}<span class="brand-dot" aria-hidden="true">.</span></a>
<nav aria-label="Main navigation"><a href="{home}#research">Research</a><a href="{home}#publications">Publications</a><a href="{prefix}cv/">CV</a><a href="{home}#contact">Contact</a></nav>
</div></header>'''


def section_title(title, extra=""):
    return f'<div class="section-heading"><h2>{title}</h2>{extra}</div>'


def biography(profile):
    paragraphs = profile["about"]
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    rendered = []
    for paragraph in paragraphs:
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(paragraph))
        rendered.append(f'<p>{text}</p>')
    return "".join(rendered)


def news(profile):
    rows = ""
    for item in profile["news"]:
        label = esc(item["text"])
        if item["url"]:
            label = external(item["url"], label)
        rows += f'<li><span class="news-date">{esc(item["date"])}</span><span>{label}</span></li>'
    return f'<section class="news-section" aria-labelledby="news-title"><h2 id="news-title">Recent updates</h2><ul class="news-list">{rows}</ul></section>'


def research(profile):
    items = ""
    for i, item in enumerate(profile["research"], 1):
        tags = "".join(f'<li>{esc(tag)}</li>' for tag in item["methods"])
        link = f'<a class="text-link" href="#pub-{esc(item["publication"])}">Related publication</a>' if item["publication"] else '<span class="current-focus">Research direction</span>'
        items += f'''<article class="research-item"><span class="research-index" aria-hidden="true">0{i}</span>
<p class="eyebrow">{esc(item['label'])}</p><h3>{esc(item['title'])}</h3><p>{esc(item['text'])}</p>
<ul class="method-tags" aria-label="Research topics">{tags}</ul>{link}</article>'''
    return f'<section id="research" class="content-section research-section">{section_title("Research")}<div class="research-grid">{items}</div></section>'


def publication(profile, pub, prefix, full=False):
    author_line = esc(pub["display_authors"]).replace(esc(profile["name"]), f'<strong>{esc(profile["name"])}</strong>')
    title = external(pub["url"], esc(pub["title"])) if pub["url"] else esc(pub["title"])
    links = ""
    if pub["doi"]:
        links += external("https://doi.org/" + pub["doi"], "DOI", "paper-link")
    if pub["code"]:
        links += external(pub["code"], "Code", "paper-link")
    links += f'<a class="paper-link" href="{prefix}citations/{esc(pub["id"])}.bib" download>BibTeX</a>'
    detail = f'<details><summary>Summary &amp; contribution</summary><p>{esc(pub["summary"])}</p><p><strong>My contribution.</strong> {esc(pub["contribution"])}</p></details>'
    volume = f' · {esc(pub["volume"])}: {esc(pub["pages"])}' if pub.get("volume") else ""
    image = f'<img class="paper-cover" src="{prefix}assets/{esc(pub["image"])}" alt="Trends in Genetics July 2025 cover featuring LINE-1 elements" width="591" height="768" loading="lazy">' if pub.get("image") and not full else ""
    return f'''<article id="pub-{esc(pub['id'])}" class="publication{' has-cover' if image else ''}">
<div class="paper-year">{pub['year']}</div><div class="paper-body"><p class="paper-meta"><span class="journal">{esc(pub['journal'])}</span>{volume}<span class="author-note">{esc(pub['note'])}</span></p>
<h3>{title}</h3><p class="paper-authors">{author_line}</p><div class="paper-actions">{links}</div>{detail}</div>{image}</article>'''


def publications(profile, prefix):
    items = "".join(publication(profile, pub, prefix) for pub in profile["publications"])
    return f'''<section id="publications" class="content-section publications-section">
{section_title('Publications', '<span class="section-note">2024–2026</span>')}
<p class="contribution-note">* Equal contribution. Author lists are abbreviated.</p><div class="publication-list">{items}</div></section>'''


def timeline(items):
    return '<ol class="timeline">' + "".join(f'''<li><span class="timeline-date">{esc(item['period'])}</span><div><h4>{esc(item['title'])}</h4><p>{esc(item['institution'])}</p><p class="secondary">{esc(item['detail'])}</p></div></li>''' for item in items) + '</ol>'


def background(profile, prefix):
    return f'''<section id="background" class="content-section background-section">
{section_title('Background', f'<a class="text-link" href="{prefix}cv/">Full curriculum vitae</a>')}
<div class="background-grid"><div><h3>Experience</h3>{timeline(profile['positions'])}</div><div><h3>Education</h3>{timeline(profile['education'])}</div></div></section>'''


def contact(profile):
    return f'''<section id="contact" class="content-section contact-section"><div><p class="eyebrow">Connect</p><h2>Research &amp; conversations.</h2><p>Find my research, code and professional profile here.</p></div>{socials(profile)}</section>'''


def footer(profile):
    return f'<footer class="site-footer"><span>© {profile["updated"][:4]} {esc(profile["name"])}</span><span>Updated <time datetime="{profile["updated"]}">{profile["updated"]}</time></span></footer>'


def cover_feature(profile, prefix):
    pub = next(p for p in profile["publications"] if p.get("image"))
    return f'''<figure class="cover-feature"><a href="#pub-{esc(pub['id'])}" aria-label="Read about the LINE-1 cover review"><img src="{prefix}assets/{esc(pub['image'])}" alt="Trends in Genetics July 2025 cover: LINE-1 elements reshape the human genomic landscape" width="591" height="768"></a>
<figcaption><span class="eyebrow">Featured review</span><span>Trends in Genetics · 2025</span><small>Cover image: Cell Press</small></figcaption></figure>'''


def research_lenses():
    diagrams = {
        'line1': '''<svg viewBox="0 0 480 240" aria-hidden="true"><path class="genome-track" d="M28 165H452"/><path class="contact-arc" d="M106 154C115 16 353 16 374 154"/><rect class="locus-a" x="48" y="145" width="112" height="38" rx="3"/><rect class="locus-b" x="319" y="145" width="126" height="38" rx="3"/><text x="104" y="219" text-anchor="middle">LINE-1</text><text x="382" y="219" text-anchor="middle">Target gene</text><text class="diagram-label" x="240" y="31" text-anchor="middle">Long-range contact</text></svg>''',
        'ankrd11': '''<svg viewBox="0 0 480 240" aria-hidden="true"><ellipse class="condensate" cx="240" cy="115" rx="159" ry="78"/><text x="240" y="78" text-anchor="middle">ANKRD11 condensate</text><path class="genome-track" d="M28 165H452"/><rect class="locus-b" x="113" y="149" width="254" height="33" rx="3"/><path class="transcription-mark" d="M142 116H189m-12-8 12 8-12 8M215 116H262m-12-8 12 8-12 8"/><path class="safeguard" d="M295 94V137"/><text class="diagram-label" x="240" y="220" text-anchor="middle">Hypertranscribed gene</text></svg>''',
        'ai': '''<svg viewBox="0 0 480 240" aria-hidden="true"><path class="model-connection" d="M108 56 214 110M108 114H214M108 172 214 130M287 120H374"/><rect class="input-locus" x="34" y="39" width="76" height="34" rx="4"/><rect class="input-locus" x="34" y="97" width="76" height="34" rx="4"/><rect class="input-locus" x="34" y="155" width="76" height="34" rx="4"/><text x="72" y="64" text-anchor="middle">E1</text><text x="72" y="122" text-anchor="middle">E2</text><text x="72" y="180" text-anchor="middle">E3</text><rect class="regulatory-model" x="214" y="82" width="74" height="76" rx="6"/><text x="251" y="128" text-anchor="middle">AI</text><rect class="locus-b" x="374" y="104" width="74" height="34" rx="3"/><text class="diagram-label" x="74" y="225" text-anchor="middle">Enhancers</text><text class="diagram-label" x="250" y="203" text-anchor="middle">Interpretable</text><text class="diagram-label" x="250" y="227" text-anchor="middle">model</text><text class="diagram-label" x="411" y="79" text-anchor="middle">Gene</text></svg>''',
    }
    lenses = [
        ('line1', 'LINE-1', 'Mobile DNA. Distal effects.', 'LINE-1 transcription promotes long-range chromatin contacts and distal gene activation.', 'Nature Genetics · 2024', '#pub-line1'),
        ('ankrd11', 'ANKRD11', 'A safeguard for transcription.', 'ANKRD11 condensates restrict transcription at hypertranscribed developmental genes.', 'Cell · 2026', '#pub-ankrd11'),
        ('ai', 'Regulatory AI', 'From mechanism to models.', 'My current direction: interpretable models of how cis-regulatory information shapes gene expression.', 'Research direction', '#research'),
    ]
    buttons, panels = '', ''
    for i, (key, label, title, text, source, target) in enumerate(lenses):
        buttons += f'<button id="lens-{key}" type="button" role="tab" aria-controls="lens-panel-{key}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}" data-lens="{key}">{label}</button>'
        panels += f'''<section id="lens-panel-{key}" class="lens-panel" role="tabpanel" aria-labelledby="lens-{key}" tabindex="0"{'' if i == 0 else ' hidden'}><div class="lens-figure">{diagrams[key]}</div><h2>{title}</h2><p>{text}</p><a class="lens-source" href="{target}">{source}</a></section>'''
    return f'''<div class="research-lenses"><div class="lens-topline"><span>Research, in focus</span><span class="concept-label">Conceptual models</span></div><div class="lens-tabs" role="tablist" aria-label="Explore research themes">{buttons}</div>{panels}</div>'''


def editorial_cover(profile, prefix):
    pub = next(p for p in profile['publications'] if p.get('image'))
    return f'''<section class="editorial-cover" aria-labelledby="cover-story-title"><figure><a href="#pub-{esc(pub['id'])}"><img src="{prefix}assets/{esc(pub['image'])}" alt="Trends in Genetics cover showing a genomic landscape through the Great Wall of China" width="591" height="768" loading="lazy"></a><figcaption>{esc(pub['image_credit'])}</figcaption></figure><div class="cover-story"><p class="eyebrow">On the cover · July 2025</p><h2 id="cover-story-title">A broader view<br>of <em>LINE-1.</em></h2><p>Beyond retrotransposition, LINE-1 elements participate in genome regulation, chromatin organization and development. Our review brings these roles into a common conceptual framework.</p><p class="cover-authorship">Xiufeng Li &amp; Nian Liu<br><span>Trends in Genetics · First author</span></p><a class="cover-read" href="#pub-{esc(pub['id'])}">Read the review</a></div></section>'''


def render_editorial(profile, prefix, preview):
    canonical = profile['site_url'].rstrip('/') + '/' if profile['site_url'] and not preview else ''
    html_start = head(profile, prefix, canonical=canonical, robots='noindex, nofollow' if preview else '', styles=('editorial.css',))
    return html_start + f'''<body class="theme-editorial editorial-v2">{header(profile, prefix)}<main id="main"><section id="about" class="hero"><div class="hero-inner"><div class="hero-copy"><p class="eyebrow">Computational &amp; regulatory genomics</p><h1>The regulatory<br>logic of the<br><em>genome.</em></h1><p class="editorial-name">{esc(profile['name'])}</p><p class="hero-intro">I study how transposable elements and chromatin architecture control gene expression, and how interpretable AI can help explain that regulatory logic.</p><p class="hero-affiliation">{esc(profile['role'])}<br>{esc(profile['affiliation'])}</p><div class="hero-links"><a class="primary-link" href="#research">Explore my research</a><a href="{prefix}cv/">Curriculum vitae</a></div></div>{research_lenses()}</div></section><div class="main-content"><section class="about-section" aria-labelledby="about-title"><div><h2 id="about-title">From LINE-1<br>to regulatory AI.</h2></div><div>{biography(profile)}</div></section>{research(profile)}{editorial_cover(profile, prefix)}{publications(profile, prefix)}{background(profile, prefix)}{news(profile)}{contact(profile)}</div></main>{footer(profile)}<script src="{prefix}assets/editorial.js" defer></script></body></html>'''


def render_site(profile, theme, prefix="", preview=False):
    if theme == 'editorial':
        return render_editorial(profile, prefix, preview)
    canonical = profile["site_url"].rstrip("/") + "/" if profile["site_url"] and not preview else ""
    start = head(profile, prefix, canonical=canonical, robots="noindex, nofollow" if preview else "")
    start += f'<body class="theme-{theme}">' + header(profile, prefix)
    bio = biography(profile)
    if theme == "classic":
        start += f'''<div class="classic-layout"><aside class="profile-sidebar" aria-label="Profile">
<div class="initials" aria-hidden="true">{esc(profile['initials'])}</div><h1>{esc(profile['name'])}</h1><p class="sidebar-role">{esc(profile['role'])}</p><p class="secondary">{esc(profile['affiliation'])}</p><div class="sidebar-rule"></div><p class="sidebar-topics">Regulatory genomics<br>Chromatin architecture<br>Interpretable AI</p>{socials(profile, 'sidebar-links')}<a class="cv-link" href="{prefix}cv/">Curriculum vitae</a></aside>
<main id="main" class="classic-main"><section id="about" class="classic-about"><p class="eyebrow">Computational &amp; regulatory genomics</p><h2>About me</h2><p class="intro">{esc(profile['intro'])}</p>{bio}</section>'''
        start += news(profile) + research(profile) + publications(profile, prefix) + background(profile, prefix) + contact(profile) + '</main></div>'
    else:
        heading = 'The regulatory logic<br class="desktop-break"> of the genome.' if theme == 'editorial' else esc(profile['name']) + '<span class="name-period" aria-hidden="true">.</span>'
        statement = esc(profile['name']) if theme == 'editorial' else 'Understanding gene regulation,<br class="desktop-break"> from mechanism to models.'
        start += f'''<main id="main"><section id="about" class="hero"><div class="hero-inner"><div class="hero-copy"><p class="eyebrow">Regulatory genomics &amp; interpretable AI</p><h1>{heading}</h1><p class="hero-statement">{statement}</p><p class="hero-intro">{esc(profile['intro'])}</p><p class="hero-affiliation">{esc(profile['role'])}<span aria-hidden="true"> · </span>{esc(profile['affiliation'])}</p><div class="hero-links"><a class="primary-link" href="#publications">View publications</a><a href="{prefix}cv/">Curriculum vitae</a></div></div>{cover_feature(profile, prefix)}</div></section>
<div class="main-content"><section class="about-section" aria-labelledby="about-title"><div><p class="eyebrow">About</p><h2 id="about-title">A computational lens on<br class="desktop-break"> biological mechanisms.</h2></div><div>{bio}</div></section>'''
        if theme == "minimal":
            start += news(profile)
        start += research(profile) + publications(profile, prefix) + background(profile, prefix)
        if theme == "editorial":
            start += news(profile)
        start += contact(profile) + '</div></main>'
    return start + footer(profile) + '</body></html>'


def cv_page(profile):
    listing = "".join(publication(profile, p, "../", full=True) for p in profile["publications"])
    awards = "".join(f'<li><span>{esc(a["year"])}</span><div>{esc(a["title"])}</div></li>' for a in profile["awards"])
    talks = "".join(f'<li><span>{esc(a["year"])}</span><div><strong>{esc(a["title"])}</strong><p>{esc(a["detail"])}</p></div></li>' for a in profile["presentations"])
    items = lambda key: '<ul class="plain-list">' + "".join(f'<li>{esc(text)}</li>' for text in profile[key]) + '</ul>'
    return head(profile, "../", title=profile['name'] + ' | Curriculum Vitae') + f'''<body class="theme-minimal cv-page">{header(profile, '../', '../index.html')}<main id="main" class="cv-main"><div class="cv-heading"><div><p class="eyebrow">Curriculum vitae</p><h1>{esc(profile['name'])}</h1><p>{esc(profile['role'])} · {esc(profile['affiliation'])}</p></div><button type="button" class="print-button" data-print>Print / Save PDF</button></div>
{socials(profile)}<section><h2>Research interests</h2><p>{esc(profile['intro'])}</p><p>{esc(profile['direction'])}</p></section>
<section><h2>Academic positions</h2>{timeline(profile['positions'])}</section><section><h2>Education</h2>{timeline(profile['education'])}</section>
<section><h2>Publications</h2><p class="contribution-note">* Equal contribution. Author lists are abbreviated; complete authors are provided in BibTeX.</p>{listing}</section>
<section><h2>Honors &amp; awards</h2><ul class="cv-records">{awards}</ul></section><section><h2>Selected presentations</h2><ul class="cv-records">{talks}</ul></section>
<section><h2>Teaching &amp; mentoring</h2>{items('teaching')}</section><section><h2>Service &amp; outreach</h2>{items('service')}</section></main>{footer(profile)}<script src="../assets/site.js" defer></script></body></html>'''


def preview_page(profile):
    options = [
        ("a", "经典学术", "Classic Academic", "固定资料侧栏，紧凑的论文与履历。", "适合：论文、学术求职", "https://academicpages.github.io/"),
        ("b", "极简现代", "Minimal Scholar", "留白、清晰排版和完整论文信息。", "适合：个人学术主页", "https://alshedivat.github.io/al-folio/"),
        ("c", "研究作品集", "Research Editorial", "互动研究示意、深色开场与论文特写。", "适合：研究展示、合作交流", "https://hugo-apero.netlify.app/")
    ]
    selected = THEMES[profile['theme']]
    selected_name = next(name for letter, name, *_ in options if letter == selected)
    selected_title = f'{selected.upper()} · {selected_name}'
    cards = ""
    for letter, name, en, description, suit, reference in options:
        cards += f'''<article class="option-card" data-option="{letter}"><div class="option-info"><span class="option-letter">{letter.upper()}</span><div><h2>{name}</h2><p>{en}</p></div>{'<span class="recommended">当前方案</span>' if letter == selected else ''}</div>
<div class="mini-preview" aria-hidden="true"><iframe src="{letter}/" title="{esc(en)} 缩略预览" tabindex="-1" inert loading="lazy"></iframe></div><div class="option-details"><p>{description}</p><span>{suit}</span><div class="option-actions"><button type="button" data-theme="{letter}" aria-pressed="{'true' if letter == selected else 'false'}">预览 {letter.upper()}</button><a href="{letter}/" target="_blank" rel="noopener">完整查看</a></div><a class="reference-link" href="{reference}" target="_blank" rel="noopener noreferrer">风格参考：{('Hugo Apéro' if letter == 'c' else ('Academic Pages' if letter == 'a' else 'al-folio'))}</a></div></article>'''
    return head(profile, "../", title="Xiufeng Li · 学术网站设计选项", lang="zh-CN", robots="noindex, nofollow") + f'''<body class="preview-page"><main id="main" class="preview-main"><header class="preview-heading"><a class="preview-home" href="../">XL<span aria-hidden="true">.</span></a><p class="eyebrow">学术网站 · 设计预览</p><h1>同一个研究者，三种呈现方式。</h1><p>已使用 CV 中的研究经历与论文制作。选择风格，查看真实页面。</p></header><div class="option-grid">{cards}</div>
<section class="live-preview" aria-labelledby="preview-title"><div class="preview-toolbar"><h2 id="preview-title" aria-live="polite">{selected_title}</h2><div class="viewport-controls" aria-label="预览尺寸"><button type="button" data-viewport="desktop" aria-pressed="true">桌面</button><button type="button" data-viewport="mobile" aria-pressed="false">手机</button></div><a id="open-preview" href="{selected}/" target="_blank" rel="noopener">独立打开</a></div><div class="live-preview-surface"><iframe id="live-frame" src="{selected}/" title="{selected_title}学术网站" height="1000"></iframe></div></section><p class="preview-footnote">三套布局共用同一份内容；正式网站的默认风格可在配置中切换。预览页仅用于比较设计。</p></main><script src="../assets/preview.js" defer></script></body></html>'''


def bibtex(pub):
    def bib(value):
        value = str(value).replace("\\", "\\textbackslash{}")
        return value.replace("{", "\\{").replace("}", "\\}").replace("&", "\\&").replace("%", "\\%").replace("–", "--")
    fields = {"title": pub["title"], "author": " and ".join(pub["authors"]), "journal": pub["journal"], "year": pub["year"]}
    for key in ("volume", "pages", "doi", "url"):
        if pub.get(key):
            fields[key] = pub[key]
    return '@article{' + pub['id'] + ',\n' + ',\n'.join(f'  {key} = {{{bib(value)}}}' for key, value in fields.items()) + '\n}\n'


def write(path, contents):
    file = OUT / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(contents, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=THEMES, help="Override the theme without editing profile.json")
    parser.add_argument("--include-previews", action="store_true", help="Include the local design comparison pages")
    args = parser.parse_args()
    profile = json.loads((ROOT / "content/profile.json").read_text(encoding="utf-8"))
    theme = args.theme or profile["theme"]
    if theme not in THEMES:
        raise ValueError("theme must be classic, minimal or editorial")
    date.fromisoformat(profile["updated"])
    if profile["site_url"] and urlsplit(profile["site_url"]).scheme not in {"https", "http"}:
        raise ValueError("site_url must be an http(s) URL or empty")
    ids = [p["id"] for p in profile["publications"]]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"[a-z0-9-]+", p) for p in ids):
        raise ValueError("Publication IDs must be unique URL-safe names")
    if OUT.is_symlink():
        raise ValueError("_site must not be a symlink")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    write("index.html", render_site(profile, theme))
    write("cv/index.html", cv_page(profile))
    write(".nojekyll", "")
    for pub in profile["publications"]:
        write(f'citations/{pub["id"]}.bib', bibtex(pub))
    write("citations/all.bib", "\n".join(bibtex(p) for p in profile["publications"]))
    if profile["site_url"]:
        base = profile["site_url"].rstrip("/")
        urls = "".join(f'<url><loc>{esc(base + route)}</loc><lastmod>{profile["updated"]}</lastmod></url>' for route in ("/", "/cv/"))
        write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    if args.include_previews:
        write("preview/index.html", preview_page(profile))
        for option, letter in THEMES.items():
            write(f"preview/{letter}/index.html", render_site(profile, option, "../../", preview=True))
    print(f"Built {theme} website in {OUT}")
    print(f"Design previews: {'included' if args.include_previews else 'excluded'}")


if __name__ == "__main__":
    main()

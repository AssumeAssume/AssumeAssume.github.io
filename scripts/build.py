#!/usr/bin/env python3
"""Build an academic website with Python's standard library."""
import argparse
import base64
import binascii
import hashlib
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from locus import research_locus

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
THEMES = {"classic": "a", "minimal": "b", "editorial": "c"}
CV_LOGOS = {
    "vib": "vib.png",
    "ku-leuven": "ku-leuven.svg",
    "tsinghua": "tsinghua.jpg",
    "cas": "cas.png",
    "big": "big.png",
    "dlut": "dlut-emblem.png",
}


def esc(value):
    return html.escape(str(value), quote=True)


UNBREAKABLE = re.compile(r"\b(?:Dr|Prof)\. [A-Z][\w-]+(?: [A-Z][\w-]+)?|\bKU Leuven\b|\bet al\.")


def prose(value):
    """Escape running text, keeping personal names and fixed phrases on one line."""
    text = UNBREAKABLE.sub(lambda match: match.group(0).replace(" ", "\u00a0"), str(value))
    return esc(text).replace("\u00a0", "&nbsp;")


def author_line(profile, pub):
    """Keep each abbreviated author name on one line and highlight the site owner."""
    names = ", ".join(esc(name).replace(" ", "&nbsp;") for name in pub["display_authors"].split(", "))
    owner = esc(profile["name"]).replace(" ", "&nbsp;")
    return names.replace(owner, f"<strong>{owner}</strong>")


def external(url, label, css=""):
    if urlsplit(url).scheme not in {"https", "http"}:
        raise ValueError(f"Unsupported URL: {url}")
    return f'<a class="{esc(css)}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label}</a>'


def email_link(profile):
    address = profile.get("email", "")
    if not address:
        return ""
    if isinstance(address, dict):
        try:
            user = base64.b64decode(address["user"], validate=True).decode("ascii")
            domain = base64.b64decode(address["domain"], validate=True).decode("ascii")
            address = user + "@" + domain
        except (KeyError, TypeError, ValueError, UnicodeError, binascii.Error) as error:
            raise ValueError("email must contain valid base64 user and domain fields") from error
    if not isinstance(address, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", address):
        raise ValueError("email must be a plain address, an encoded user/domain object, or empty")
    user, domain = address.split("@")
    encoded_user = base64.b64encode(user.encode("ascii")).decode("ascii")
    encoded_domain = base64.b64encode(domain.encode("ascii")).decode("ascii")
    readable_address = user + " [at] " + domain.replace(".", " [dot] ")
    return f'<span class="email-contact"><button type="button" class="email-link" data-email-user="{encoded_user}" data-email-domain="{encoded_domain}">Email me</button><small class="email-fallback">{esc(readable_address)}</small></span>'


def socials(profile, css="social-links", include_email=False):
    email = email_link(profile) if include_email else ""
    return f'<div class="{esc(css)}">' + email + "".join(external(item["url"], esc(item["label"])) for item in profile["links"]) + "</div>"


def head(profile, prefix, title=None, lang="en", canonical="", robots="", styles=()):
    description = profile["description"]
    metadata = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    if robots:
        metadata += f'<meta name="robots" content="{esc(robots)}">'
    if canonical:
        metadata += f'<meta property="og:url" content="{esc(canonical)}">'
    share_image = profile.get("share_image") or profile.get("portrait")
    if share_image and profile["site_url"]:
        image_url = profile["site_url"].rstrip("/") + "/assets/" + share_image
        image_alt = (profile.get("share_image_alt") or f'{profile["name"]} · Gene regulation') if profile.get("share_image") else f'Portrait of {profile["name"]}'
        card_type = "summary_large_image" if profile.get("share_image") else "summary"
        metadata += f'<meta property="og:image" content="{esc(image_url)}"><meta property="og:image:alt" content="{esc(image_alt)}"><meta name="twitter:card" content="{card_type}"><meta name="twitter:image" content="{esc(image_url)}"><meta name="twitter:image:alt" content="{esc(image_alt)}">'
        if profile.get("share_image"):
            metadata += '<meta property="og:image:type" content="image/png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
    stylesheets = ''.join(
        f'<link rel="stylesheet" href="{prefix}assets/{esc(style)}?v={hashlib.sha256((ROOT / "assets" / style).read_bytes()).hexdigest()[:12]}">'
        for style in ('site.css', *styles)
    )
    contact_script = ''
    if profile.get("email"):
        version = hashlib.sha256((ROOT / "assets/contact.js").read_bytes()).hexdigest()[:12]
        contact_script = f'<script src="{prefix}assets/contact.js?v={version}" defer></script>'
    visits = profile.get("visits") or {}
    if visits.get("endpoint"):
        version = hashlib.sha256((ROOT / "assets/visits.js").read_bytes()).hexdigest()[:12]
        host = urlsplit(profile["site_url"]).hostname
        contact_script += f'<script src="{prefix}assets/visits.js?v={version}" data-endpoint="{esc(visits["endpoint"])}" data-site="{esc(visits["site"])}" data-host="{esc(host)}" defer></script>'
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title or profile['name'] + ' | Regulatory Genomics')}</title>
<meta name="description" content="{esc(description)}"><meta name="theme-color" content="#F6F4EE">
<meta property="og:title" content="{esc(title or profile['name'])}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website">
{metadata}<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
{stylesheets}{contact_script}</head>'''


def header(profile, prefix="", home=""):
    return f'''<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="header-inner">
<a class="brand" href="{home or '#about'}">{esc(profile['name'])}<span class="brand-dot" aria-hidden="true">.</span></a>
<nav aria-label="Main navigation"><a href="{home}#research">Research</a><a href="{prefix}publications/">Publications</a><a href="{prefix}cv/">CV</a><a href="{home}#contact">Contact</a></nav>
</div></header>'''


def section_title(title, extra=""):
    return f'<div class="section-heading"><h2>{title}</h2>{extra}</div>'


def biography(profile):
    paragraphs = profile["about"]
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    return formatted_paragraphs(paragraphs)


def inline_format(text, allow_bold=True, allow_links=True):
    """Render the two supported inline formats while escaping all plain text."""
    patterns = []
    if allow_bold:
        patterns.append(r"\*\*(?P<bold>.+?)\*\*")
    if allow_links:
        patterns.append(r"\[(?P<label>[^\[\]\n]+)\]\((?P<url>[^\s<>()]+)\)")
    if not patterns:
        return prose(text)
    rendered = []
    position = 0
    for match in re.finditer("|".join(patterns), text):
        rendered.append(prose(text[position:match.start()]))
        if match.groupdict().get("bold") is not None:
            rendered.append('<strong>' + inline_format(match.group("bold"), allow_bold=False, allow_links=allow_links) + '</strong>')
        else:
            url = match.group("url")
            try:
                parts = urlsplit(url)
                valid_url = parts.scheme in {"https", "http"} and bool(parts.netloc)
            except ValueError:
                valid_url = False
            if valid_url:
                rendered.append(external(url, inline_format(match.group("label"), allow_bold=allow_bold, allow_links=False)))
            else:
                rendered.append(prose(match.group(0)))
        position = match.end()
    rendered.append(prose(text[position:]))
    return ''.join(rendered)


def formatted_paragraphs(paragraphs):
    return ''.join(f'<p>{inline_format(paragraph)}</p>' for paragraph in paragraphs)


def news(profile):
    rows = ""
    for item in profile["news"]:
        label = prose(item["text"])
        if item["url"]:
            label = external(item["url"], label + '&nbsp;<span class="link-arrow" aria-hidden="true">↗</span>')
        rows += f'<li><span class="news-date">{esc(item["date"])}</span><span>{label}</span></li>'
    return f'<section id="updates" class="news-section" aria-labelledby="news-title"><h2 id="news-title">Recent updates</h2><ul class="news-list">{rows}</ul></section>'


def research(profile):
    items = ""
    for i, item in enumerate(profile["research"], 1):
        tags = "".join(f'<li>{esc(tag)}</li>' for tag in item["methods"])
        link = f'<a class="text-link" href="#pub-{esc(item["publication"])}">Related publication</a>' if item["publication"] else '<span class="current-focus">Research direction</span>'
        items += f'''<article class="research-item"><span class="research-index" aria-hidden="true">0{i}</span>
<p class="eyebrow">{esc(item['label'])}</p><h3>{esc(item['title'])}</h3><p>{esc(item['text'])}</p>
<ul class="method-tags" aria-label="Research topics">{tags}</ul>{link}</article>'''
    return f'<section id="research" class="content-section research-section">{section_title("Research")}<div class="research-grid">{items}</div></section>'


def publication_keywords(pub):
    keywords = pub.get("keywords", [])
    if not keywords:
        return ""
    items = []
    for keyword in keywords:
        if not isinstance(keyword, str):
            raise ValueError("publication keywords must be plain text strings")
        items.append(f'<li>{esc(keyword)}</li>')
    return '<div class="publication-keywords"><span class="keywords-label">Keywords</span><ul>' + ''.join(items) + '</ul></div>'


def paper_links(pub, prefix, css):
    """Shared Paper / Code / BibTeX actions for every publication listing."""
    url = pub["url"] or ("https://doi.org/" + pub["doi"] if pub["doi"] else "")
    links = external(url, 'Paper <span aria-hidden="true">↗</span>', css) if url else ""
    if pub["code"]:
        links += external(pub["code"], 'Code <span aria-hidden="true">↗</span>', css)
    return links + f'<a class="{esc(css)}" href="{prefix}citations/{esc(pub["id"])}.bib" download>BibTeX</a>'


def publication(profile, pub, prefix, full=False):
    authors = author_line(profile, pub)
    title = external(pub["url"], esc(pub["title"])) if pub["url"] else esc(pub["title"])
    links = paper_links(pub, prefix, "paper-link")
    detail = f'<details><summary>Summary &amp; contribution</summary><p>{esc(pub["summary"])}</p><p><strong>My contribution.</strong> {esc(pub["contribution"])}</p></details>'
    volume = f' · {esc(pub["volume"])}: {esc(pub["pages"])}' if pub.get("volume") else ""
    image = f'<img class="paper-cover" src="{prefix}assets/{esc(pub["image"])}" alt="Trends in Genetics July 2025 cover featuring LINE-1 elements" width="591" height="768" loading="lazy">' if pub.get("image") and not full else ""
    return f'''<article id="pub-{esc(pub['id'])}" class="publication{' has-cover' if image else ''}">
<div class="paper-year">{pub['year']}</div><div class="paper-body"><p class="paper-meta"><span class="journal">{esc(pub['journal'])}</span>{volume}<span class="author-note">{esc(pub['note'])}</span></p>
<h3>{title}</h3><p class="paper-authors">{authors}</p><div class="paper-actions">{links}</div>{detail}{publication_keywords(pub)}</div>{image}</article>'''


def publications(profile, prefix):
    items = "".join(publication(profile, pub, prefix) for pub in profile["publications"])
    return f'''<section id="publications" class="content-section publications-section">
{section_title('Publications', '<span class="section-note">2024–2026</span>')}
<p class="contribution-note">* Equal contribution. Author lists are abbreviated.</p><div class="publication-list">{items}</div></section>'''


def timeline(items, show_logos=False, prefix=""):
    rows = []
    for item in items:
        detail = f'<p class="secondary">{prose(item["detail"])}</p>' if item.get('detail') else ''
        funding = f'<p class="secondary">{prose(item["funding"])}</p>' if item.get('funding') else ''
        copy = f'<h4>{prose(item["title"])}</h4><p>{prose(item["institution"])}</p>{detail}{funding}'
        if show_logos and item.get('logos'):
            marks = []
            for logo in item['logos']:
                if logo not in CV_LOGOS:
                    raise ValueError(f"Unknown CV logo: {logo}")
                marks.append(f'<span class="timeline-logo timeline-logo--{logo}"><img src="{prefix}assets/logos/{CV_LOGOS[logo]}" alt="" loading="lazy"></span>')
            copy = f'<div class="timeline-entry"><div class="timeline-copy">{copy}</div><div class="timeline-logos" aria-hidden="true">{"".join(marks)}</div></div>'
        rows.append(f'''<li><span class="timeline-date">{esc(item['period'])}</span><div>{copy}</div></li>''')
    return '<ol class="timeline">' + ''.join(rows) + '</ol>'


def background(profile, prefix):
    return f'''<section id="background" class="content-section background-section">
{section_title('Background', f'<a class="text-link" href="{prefix}cv/">Full curriculum vitae</a>')}
<div class="background-grid"><div><h3>Experience</h3>{timeline(profile['positions'])}</div><div><h3>Education</h3>{timeline(profile['education'])}</div></div></section>'''


def contact(profile):
    return f'''<section id="contact" class="content-section contact-section"><div><p class="eyebrow">Connect</p><h2>Research &amp; conversations.</h2><p>Find my research, code and professional profile here.</p></div>{socials(profile, include_email=True)}</section>'''


def footer(profile):
    return f'<footer class="site-footer"><span>© {profile["updated"][:4]} {esc(profile["name"])}</span><span>Updated <time datetime="{profile["updated"]}">{profile["updated"]}</time></span></footer>'


def cover_feature(profile, prefix):
    pub = next(p for p in profile["publications"] if p.get("image"))
    return f'''<figure class="cover-feature"><a href="#pub-{esc(pub['id'])}" aria-label="Read about the LINE-1 cover review"><img src="{prefix}assets/{esc(pub['image'])}" alt="Trends in Genetics July 2025 cover: LINE-1 elements reshape the human genomic landscape" width="591" height="768"></a>
<figcaption><span class="eyebrow">Featured review</span><span>Trends in Genetics · 2025</span><small>Cover image: Cell Press</small></figcaption></figure>'''


def notebook_header(profile, prefix="", home="", current=""):
    pages = [
        ("about", f"{home}#about-me", "About"),
        ("research", f"{home}#research", "Research"),
        ("publications", f"{prefix}publications/", "Publications"),
        ("cv", f"{prefix}cv/", "CV"),
        ("contact", f"{home}#contact", "Contact"),
    ]
    links = "".join(
        f'<a href="{href}"' + (' aria-current="page"' if key == current else '') + f'>{label}</a>'
        for key, href, label in pages
    )
    return f'''<a class="skip-link" href="#main">Skip to content</a><header class="site-header"><div class="header-inner"><a class="brand" href="{home or '#about'}">{esc(profile['name'])}</a><nav aria-label="Main navigation">{links}</nav></div></header>'''


def privacy_text(profile):
    """The privacy statement, published only while visits are being counted."""
    visits = profile.get("visits") or {}
    return visits.get("privacy", "") if visits.get("endpoint") else ""


def notebook_footer(profile, prefix=""):
    github = next(link['url'] for link in profile['links'] if link['label'] == 'GitHub')
    privacy = f'<a href="{prefix}privacy/">Privacy</a> · ' if privacy_text(profile) else ''
    return f'<footer class="site-footer"><span>© {profile["updated"][:4]} {esc(profile["name"])} / {external(github, "AssumeAssume")}</span><span>{privacy}Updated <time datetime="{profile["updated"]}">{profile["updated"]}</time></span></footer>'


def selected_work(profile, prefix):
    papers = {p['id']: p for p in profile['publications']}
    rows = ''
    for story in profile['notebook']['selected_work']:
        pub = papers[story['publication']]
        authors = author_line(profile, pub)
        actions = paper_links(pub, prefix, 'notebook-link')
        image = ''
        if pub.get('image'):
            image = f'<figure class="work-cover"><img src="{prefix}assets/{esc(pub["image"])}" alt="Trends in Genetics July 2025 cover showing a genomic landscape through the Great Wall" width="591" height="768" loading="lazy"><figcaption>July 2025 cover · Cell Press</figcaption></figure>'
        figure = ''
        if pub.get('figure'):
            caption = f'<figcaption>{esc(pub["figure_caption"])}</figcaption>' if pub.get('figure_caption') else ''
            width, height = pub.get('figure_width', 720), pub.get('figure_height', 260)
            if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
                raise ValueError("figure dimensions must be positive integers")
            figure_version = hashlib.sha256((ROOT / 'assets' / pub['figure']).read_bytes()).hexdigest()[:12]
            figure = f'<figure class="study-figure"><img src="{prefix}assets/{esc(pub["figure"])}?v={figure_version}" alt="{esc(pub["figure_alt"])}" width="{width}" height="{height}" loading="lazy">{caption}</figure>'
        question = f'<p>{esc(story["question"])}</p>' if story.get('question') else ''
        rows += f'''<article id="pub-{esc(pub['id'])}" class="selected-study{' with-cover' if image else ''}"><div class="work-meta"><span>{pub['year']} / {esc(pub['journal'])}</span><span>{esc(pub['note'])}</span></div><div class="study-grid"><div class="study-question"><h3>{esc(story['title'])}</h3>{question}{figure}{image}</div><div class="study-result"><p class="finding">{esc(pub['summary'])}</p><p class="my-part"><strong>My part.</strong> {esc(pub['contribution'])}</p>{publication_keywords(pub)}<div class="work-actions">{actions}</div><details class="publication-details"><summary>Publication details</summary><h4>{external(pub['url'], esc(pub['title']))}</h4><p>{authors}</p><p>{esc(pub['journal'])} · {pub['year']} · DOI: {esc(pub['doi'])}</p></details></div></div></article>'''
    return f'''<section id="research" class="notebook-section selected-work"><div class="notebook-section-heading"><h2>Selected work</h2><p>Questions, discoveries, and my part in them.</p></div>{rows}<div id="publications" class="bibliography-link"><a class="notebook-link" href="{prefix}publications/">Complete publication list →</a><span>Full references and BibTeX</span></div></section>'''


def notebook_about(profile, prefix):
    paragraphs = [profile['notebook']['about_intro'], profile['about'][1], profile['about'][3]]
    return f'''<section id="about-me" class="notebook-about" aria-labelledby="about-title"><figure class="portrait"><img src="{prefix}assets/{esc(profile['portrait'])}" alt="Xiufeng Li outdoors in front of a mountain landscape" width="501" height="504"><figcaption>{esc(profile['name'])} / AssumeAssume</figcaption></figure><div class="about-copy"><h2 id="about-title">About</h2>{formatted_paragraphs(paragraphs)}<a class="notebook-link" href="{prefix}cv/">The full academic path → CV</a></div></section>'''


def currently_exploring(profile):
    return f'''<aside id="currently-exploring" class="current-exploration" aria-labelledby="currently-title"><h3 id="currently-title">Currently exploring</h3><p>{esc(profile['notebook']['currently_exploring'])}</p></aside>'''


def notebook_contact(profile, prefix):
    return f'''<section id="contact" class="notebook-contact"><div><h2>Research &amp; conversations.</h2><p>Find my papers, code, and professional profile.</p></div><div class="contact-links">{socials(profile, include_email=True)}<a class="notebook-link" href="{prefix}cv/">Curriculum vitae →</a></div></section>'''


def render_editorial(profile, prefix, preview):
    canonical = profile['site_url'].rstrip('/') + '/' if profile['site_url'] and not preview else ''
    html_start = head(profile, prefix, title=profile['name'] + ' · ' + profile['chinese_name'] + ' | Gene regulation', canonical=canonical, robots='noindex, nofollow' if preview else '', styles=('editorial.css', 'story.css'))
    notebook = profile['notebook']
    return html_start + f'''<body class="theme-editorial editorial-v2 notebook">{notebook_header(profile, prefix)}<main id="main"><section id="about" class="hero"><div class="hero-inner"><div class="hero-copy"><h1><span class="latin-name">{esc(profile['name'])}</span><span class="chinese-name" lang="zh-CN">· {esc(profile['chinese_name'])}</span></h1><p class="name-pronunciation">Pronounced like: <span>{esc(profile['pronunciation'])}</span></p><h2 class="hero-question">{esc(notebook['question'])}</h2><p class="hero-intro">{esc(notebook['intro'])}</p><p class="hero-affiliation">{esc(notebook['byline'])}</p><div class="hero-links"><a class="primary-link" href="#research">Explore my research →</a><a href="{prefix}publications/">All publications →</a></div></div>{research_locus()}</div></section><div class="main-content">{notebook_about(profile, prefix)}{news(profile)}{selected_work(profile, prefix)}{currently_exploring(profile)}{notebook_contact(profile, prefix)}</div></main>{notebook_footer(profile, prefix)}<script src="{prefix}assets/editorial.js" defer></script></body></html>'''


def publication_page(profile):
    listing = ''.join(publication(profile, p, '../', full=True) for p in profile['publications'])
    canonical = profile['site_url'].rstrip('/') + '/publications/' if profile['site_url'] else ''
    return head(profile, '../', title=profile['name'] + ' | Publications', canonical=canonical, styles=('editorial.css',)) + f'''<body class="theme-editorial editorial-v2 notebook publication-archive">{notebook_header(profile, '../', '../index.html', current='publications')}<main id="main" class="archive-main"><p class="eyebrow">Complete bibliography</p><h1>Publications</h1><p class="archive-intro">Research papers and reviews, with references, code, and contributions.</p><p class="contribution-note">* Equal contribution. Author lists are abbreviated; complete authors are provided in BibTeX.</p><div id="publications" class="publication-list">{listing}</div><a class="notebook-link" href="../index.html#research">← Back to selected work</a></main>{notebook_footer(profile, '../')}</body></html>'''


def privacy_page(profile):
    canonical = profile['site_url'].rstrip('/') + '/privacy/' if profile['site_url'] else ''
    return head(profile, '../', title=profile['name'] + ' | Privacy', canonical=canonical, styles=('editorial.css',)) + f'''<body class="notebook privacy-page">{notebook_header(profile, '../', '../index.html')}<main id="main" class="archive-main"><h1>Privacy</h1><p class="archive-intro">{esc(privacy_text(profile))}</p></main>{notebook_footer(profile, '../')}</body></html>'''


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


def render_service(profile):
    groups = []
    for entry in profile["service"]:
        if isinstance(entry, str):
            groups.append(f'<p class="outreach-note">{esc(entry)}</p>')
        else:
            journals = "".join(
                f'<li><span class="journal-badge">{esc(journal)}</span></li>'
                for journal in entry["journals"]
            )
            groups.append(
                f'<div class="reviewing-group"><p class="reviewing-role">{esc(entry["role"])}</p>'
                f'<ul class="journal-badges">{journals}</ul></div>'
            )
    return "".join(groups)


def cv_page(profile):
    listing = "".join(publication(profile, p, "../", full=True) for p in profile["publications"])
    awards = "".join(f'<li><span>{esc(a["year"])}</span><div>{prose(a["title"])}</div></li>' for a in profile["awards"])
    talks = "".join(f'<li><span>{esc(a["year"])}</span><div><strong>{prose(a["title"])}</strong><p>{prose(a["detail"])}</p></div></li>' for a in profile["presentations"])
    items = lambda key: '<ul class="plain-list">' + "".join(f'<li>{prose(text)}</li>' for text in profile[key]) + '</ul>'
    canonical = profile['site_url'].rstrip('/') + '/cv/' if profile['site_url'] else ''
    return head(profile, "../", title=profile['name'] + ' | Curriculum Vitae', canonical=canonical, styles=('editorial.css',)) + f'''<body class="notebook cv-page">{notebook_header(profile, '../', '../index.html', current='cv')}<main id="main" class="cv-main"><div class="cv-heading"><div><p class="eyebrow">Curriculum vitae</p><h1>{esc(profile['name'])}</h1><p>{prose(profile['role'])} · {prose(profile['affiliation'])}</p></div><button type="button" class="print-button" data-print>Print / Save PDF</button></div>
{socials(profile, include_email=True)}<section><h2>Research interests</h2><p>{esc(profile['intro'])}</p><p>{esc(profile['direction'])}</p></section>
<section><h2>Academic positions</h2>{timeline(profile['positions'], show_logos=True, prefix='../')}</section><section><h2>Education</h2>{timeline(profile['education'], show_logos=True, prefix='../')}</section>
<section><h2>Publications</h2><p class="contribution-note">* Equal contribution. Author lists are abbreviated; complete authors are provided in BibTeX.</p>{listing}</section>
<section><h2>Honors &amp; awards</h2><ul class="cv-records">{awards}</ul></section><section><h2>Selected presentations</h2><ul class="cv-records">{talks}</ul></section>
<section><h2>Teaching &amp; mentoring</h2>{items('teaching')}</section><section><h2>Service &amp; outreach</h2>{render_service(profile)}</section></main>{notebook_footer(profile, '../')}<script src="../assets/site.js" defer></script></body></html>'''


def preview_page(profile):
    options = [
        ("a", "经典学术", "Classic Academic", "固定资料侧栏，紧凑的论文与履历。", "适合：论文、学术求职", "https://academicpages.github.io/"),
        ("b", "极简现代", "Minimal Scholar", "留白、清晰排版和完整论文信息。", "适合：个人学术主页", "https://alshedivat.github.io/al-folio/"),
        ("c", "研究手记", "Research Notebook", "基因座批注、个人照片与精选研究。", "适合：研究展示、合作交流", "https://hugo-apero.netlify.app/")
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
    def field_value(key, value):
        value = bib(value)
        if key == "title":
            # Protect scientific names from bibliography styles that lowercase titles.
            value = re.sub(r"(?<![A-Za-z0-9])(?:ANKRD11|LINE-1|SAFB|L1)(?![A-Za-z0-9])", r"{\g<0>}", value)
        return value
    return '@article{' + pub['id'] + ',\n' + ',\n'.join(f'  {key} = {{{field_value(key, value)}}}' for key, value in fields.items()) + '\n}\n'


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
    visits = profile.get("visits") or {}
    if visits.get("endpoint") and (urlsplit(visits["endpoint"]).scheme != "https" or not profile["site_url"] or not re.fullmatch(r"[a-z0-9-]+", visits.get("site", ""))):
        raise ValueError("visits needs an https endpoint, a URL-safe site name and site_url")
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
    write("publications/index.html", publication_page(profile))
    if privacy_text(profile):
        write("privacy/index.html", privacy_page(profile))
    write(".nojekyll", "")
    for pub in profile["publications"]:
        write(f'citations/{pub["id"]}.bib', bibtex(pub))
    write("citations/all.bib", "\n".join(bibtex(p) for p in profile["publications"]))
    if profile["site_url"]:
        base = profile["site_url"].rstrip("/")
        urls = "".join(f'<url><loc>{esc(base + route)}</loc><lastmod>{profile["updated"]}</lastmod></url>' for route in ("/", "/cv/", "/publications/"))
        write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    if args.include_previews:
        write("preview/index.html", preview_page(profile))
        for option, letter in THEMES.items():
            write(f"preview/{letter}/index.html", render_site(profile, option, "../../", preview=True))
    print(f"Built {theme} website in {OUT}")
    print(f"Design previews: {'included' if args.include_previews else 'excluded'}")


if __name__ == "__main__":
    main()

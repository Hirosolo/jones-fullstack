# utils/content_processors.py


import re
from urllib.parse import urlsplit

import lxml.html
import markdown
import pymdownx.arithmatex as arithmatex
from lxml_html_clean import Cleaner, autolink_html
from lxml.html.defs import tags
from pymdownx import emoji
from pymdownx.superfences import fence_div_format

from utils.common import bytes_to_str

WEBSITE_WHITELIST = [
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "vimeo.com",
    "www.vimeo.com",
    "player.vimeo.com",
    "w.soundcloud.com",
    "googleusercontent.com",
    "imgur.com",
    "discordapp.com",
    "codesandbox.io",
    "codepen.io",
    'stackblitz.com',
]


class NewCleaner(Cleaner):
    def allow_embedded_url(self, el, url):
        if self.whitelist_tags is not None and el.tag not in self.whitelist_tags:
            return False
        scheme, netloc, path, query, fragment = urlsplit(url)
        netloc = netloc.lower().split(":", 1)[0]
        if scheme not in ("http", "https", ""):
            return False
        if netloc in self.host_whitelist:
            return True
        return False


form_tags = [
    "textarea",
    "form",
    "button",
    "select",
    "option",
    "optgroup",
    "fieldset",
    "output",
]
standard_tags = list(tags)

desc_cleaner = NewCleaner(
    page_structure=False,
    links=False,
    style=False,
    safe_attrs_only=False,
    embedded=True,
    forms=False,
    remove_unknown_tags=False,
    allow_tags=standard_tags,
    host_whitelist=WEBSITE_WHITELIST,
    remove_tags=("html", "head", "body", 'a', 'iframe', 'img', *form_tags),
    add_nofollow=False,
)

content_cleaner = NewCleaner(
    page_structure=False,
    links=False,
    style=False,
    safe_attrs_only=False,
    embedded=True,
    forms=False,
    remove_unknown_tags=False,
    allow_tags=standard_tags,
    host_whitelist=WEBSITE_WHITELIST,
    remove_tags=("html", "head", "body", *form_tags),
    add_nofollow=False,
)

_link_regexes = [
    re.compile(
        r"(?P<body>https?://(?P<host>[a-z0-9._-]+)(?:/[/\-_.,a-z0-9ốẽỷăãđýỵẻưỡầéừơẩủớỉặậờàệỗễồụểẫũạằẵỳấíỹửìôứởẹộùêếịèẳáắềĩọổâợữảúự%&?;=~:@#+]*)?(?:\([/\-_.,a-z0-9ốẽỷăãđýỵẻưỡầéừơẩủớỉặậờàệỗễồụểẫũạằẵỳấíỹửìôứởẹộùêếịèẳáắềĩọổâợữảúự%&?;=~:@#+]*\))?)",
        re.I,
    )
]


def clean_desc(html, method="html"):
    """
    Hàm này dùng để clean html của mô tả.
    Hàm này lọc các thẻ do người dùng nhập vào, chỉ giữ lại các thẻ an toàn.
    """
    if not html:
        return ""
    html = build_markdown(html)
    html = autolink_html(html, link_regexes=_link_regexes)
    html = lxml.html.fromstring(desc_cleaner.clean_html(html))

    for bq in html.xpath("//blockquote"):
        if not bq.attrib.get("class"):
            bq.attrib["class"] = "blockquote"

    for ip in html.xpath("//input"):
        if ip.attrib.get("type") not in ["checkbox", "radio"]:
            parent = ip.getparent()
            parent.remove(ip)

    # nếu có tag h1 thì chuyển thành h3
    for h in html.xpath("//h1"):
        h.tag = "h3"
    # nếu có tag h2 thì chuyển thành h4
    for h in html.xpath("//h2"):
        h.tag = "h4"

    for tb in html.xpath("//table"):
        if not tb.attrib.get("class"):
            tb.attrib["class"] = "table"
        parent = tb.getparent()
        idx = parent.index(tb)
        if parent is not None and "table-responsive" not in parent.attrib.get(
                "class", ""
        ):
            if parent.tag == "figure" and parent.attrib.get("class") == "table":
                parent.attrib["class"] = "table-responsive"
            else:
                parent.remove(tb)
                div = lxml.html.fromstring('<div class="table-responsive"></div>')
                div.insert(0, tb)
                parent.insert(idx, div)

    return bytes_to_str(lxml.html.tostring(html, encoding="utf-8", method=method))


def build_markdown(md):
    extensions = [
        "pymdownx.superfences",
        "pymdownx.inlinehilite",
        "pymdownx.tasklist",
        "pymdownx.betterem",
        "pymdownx.tilde",
        "pymdownx.keys",
        "pymdownx.smartsymbols",
        "pymdownx.emoji",
        "pymdownx.details",
        "pymdownx.escapeall",
        "pymdownx.mark",
        "pymdownx.tabbed",
        "tables",
        "toc",
    ]
    extension_configs = {
        "pymdownx.tasklist": {"custom_checkbox": True},
        "pymdownx.emoji": {
            "emoji_index": emoji.gemoji,
            "options": {
                "attributes": {
                    "class": "vd-emoji",
                    "align": "absmiddle",
                    "height": "24px",
                    "width": "24px",
                },
            },
        },
        "pymdownx.superfences": {
            "custom_fences": [
                {"name": "mermaid", "class": "mermaid", "format": fence_div_format},
                {
                    "name": "math",
                    "class": "arithmatex",
                    "format": arithmatex.fence_generic_format,
                },
            ]
        },
    }
    return markdown.markdown(
        md, extensions=extensions, extension_configs=extension_configs
    )


def clean_content(html, method="html"):
    """
    Clean HTML cho nội dung.
    Vì chủ yếu là do admin viết nên không cần lọc nhiều.
    """
    if not html:
        return ""
    html = build_markdown(html)
    html = autolink_html(html, link_regexes=_link_regexes)
    html = lxml.html.fromstring(content_cleaner.clean_html(html))

    for bq in html.xpath("//blockquote"):
        if not bq.attrib.get("class"):
            bq.attrib["class"] = "blockquote"

    for ip in html.xpath("//input"):
        if ip.attrib.get("type") not in ["checkbox", "radio"]:
            parent = ip.getparent()
            parent.remove(ip)

    for tb in html.xpath("//table"):
        if not tb.attrib.get("class"):
            tb.attrib["class"] = "table"
        parent = tb.getparent()
        idx = parent.index(tb)
        if parent is not None and "table-responsive" not in parent.attrib.get(
                "class", ""
        ):
            if parent.tag == "figure" and parent.attrib.get("class") == "table":
                parent.attrib["class"] = "table-responsive"
            else:
                parent.remove(tb)
                div = lxml.html.fromstring('<div class="table-responsive"></div>')
                div.insert(0, tb)
                parent.insert(idx, div)

    return bytes_to_str(lxml.html.tostring(html, encoding="utf-8", method=method))

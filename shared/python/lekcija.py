"""Lesson notes (private, tools/{predmet}/_source/lekcije-{razred}/NN-slug.md) → sections and HTML.

Used by scripts/build_lekcije.py (the protected lesson pages) and by lesson_quiz.py (the drawer's
"Iz udžbenika" block links to the lesson page at the section a question comes from and, in the
protected quiz, shows that section's notes). The notes are our own words; the book's text is shown
only as the page scans on the protected lesson page.

Note format: YAML frontmatter (lekcija, naslov, strane, skenovi, …), one `# title`, then `##`/`###`
sections; a book section names its pages in the heading: `## Pojava parne mašine (str. 29)`.
"""
import html as _html
import pathlib
import re

import yaml

_TR = str.maketrans("čćšđžČĆŠĐŽ", "ccsdzCCSDZ")
_PAGES = re.compile(r"\s*\((?:str\.|strana|strane)\s*([0-9]+)(?:\s*[–-]\s*([0-9]+))?[^)]*\)\s*$")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.translate(_TR).lower()).strip("-")


def note_path(root, predmet, razred, broj):
    hits = sorted((pathlib.Path(root) / "tools" / predmet / "_source" / f"lekcije-{razred}").glob(f"{int(broj):02d}-*.md"))
    return hits[0] if hits else None


def lesson_dir(predmet, razred, stem):
    """Folder of the protected lesson page, relative to the repo root."""
    return f"zasticeno/lekcije/{predmet}/{razred}/{stem}/"


def parse_note(path):
    """{fm, naslov, sections:[{level, naslov, id, strane:(od, do)|None, body}]} — `body` is the
    section's markdown without its sub-sections; the generated graf block is dropped."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = yaml.safe_load(m.group(1)) if m else {}
    text = text[m.end():] if m else text
    text = re.sub(r"<!-- graf:auto -->.*?<!-- /graf:auto -->", "", text, flags=re.S)
    sections, cur, parent_pages, seen = [], None, None, set()
    for line in text.splitlines():
        h = re.match(r"(#{1,3}) (.+)$", line)
        if h and len(h.group(1)) == 1:
            cur = None
            continue
        if h:
            level, raw = len(h.group(1)), h.group(2).strip()
            pm = _PAGES.search(raw)
            naslov = _PAGES.sub("", raw).strip() if pm else raw
            pages = (int(pm.group(1)), int(pm.group(2) or pm.group(1))) if pm else None
            if level == 2:
                parent_pages = pages
            elif not pages:
                pages = parent_pages
            sid = "o-" + slugify(naslov)
            while sid in seen:
                sid += "-2"
            seen.add(sid)
            cur = {"level": level, "naslov": naslov, "id": sid, "strane": pages, "body": ""}
            sections.append(cur)
        elif cur is not None:
            cur["body"] += line + "\n"
    return {"fm": fm or {}, "naslov": (fm or {}).get("naslov") or pathlib.Path(path).stem, "sections": sections}


def match_section(sections, odeljak, strana):
    """The section a quiz item's `iz_udzbenika` points to: by its `odeljak` name, else by its page."""
    want = slugify(re.split(r"[;—]", odeljak or "")[0])
    book = [s for s in sections if s["strane"]]
    if want:
        for s in sections:
            if slugify(s["naslov"]) == want:
                return s
        for s in sections:
            got = slugify(s["naslov"])
            if got.startswith(want) or want.startswith(got) or got.split("-")[0] == want.split("-")[0] and len(want) > 6:
                return s
        # a topic named in bold inside a section ("**Reljef** …"), then the section kinds of the notes
        word = re.split(r"[;—]", odeljak)[0].strip().lower()
        for s in sections:
            if re.search(r"\*\*" + re.escape(word), s["body"].lower()):
                return s
        kinds = {"zadat": "zadaci", "ponovi": "zadaci", "slika": "slike", "fotograf": "slike", "karta": "na-karti"}
        for k, sec in kinds.items():
            if want.startswith(k):
                hit = [s for s in sections if slugify(s["naslov"]).startswith(sec)]
                if hit:
                    return hit[0]
    if strana:
        top = [s for s in book if s["level"] == 2 and s["strane"][0] <= int(strana) <= s["strane"][1]]
        if top:
            return top[0]
    return None


# --- markdown → HTML (the subset the notes use) ---

def _inline(s, ctx):
    out, pos = [], 0
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]|\[([^\]]+)\]\(([^)]+)\)", s):
        out.append(_html.escape(s[pos:m.start()], quote=False))
        if m.group(1):
            slug = m.group(1).strip()
            out.append('<span class="pojam">' + _html.escape(m.group(2) or ctx.get("pojmovi", {}).get(slug) or slug.replace("-", " ")) + "</span>")
        else:
            label, href = m.group(3), m.group(4)
            lm = re.match(r"(?:\.\./lekcije-\d+/)?(\d\d-[^/]+)\.md$", href)
            sm = re.search(r"slike-\d+/[^/]+/([^/]+)\.md$", href)
            if lm:
                out.append(f'<a href="../{_html.escape(lm.group(1))}/">{_html.escape(label, quote=False)}</a>')
            elif sm:
                out.append(f'<a href="#sl-{_html.escape(sm.group(1))}">{_html.escape(label, quote=False)}</a>')
            elif re.match(r"https?://", href):
                out.append(f'<a href="{_html.escape(href)}" rel="noopener">{_html.escape(label, quote=False)}</a>')
            else:
                out.append(_html.escape(label, quote=False))
        pos = m.end()
    out.append(_html.escape(s[pos:], quote=False))
    t = "".join(out)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def md_to_html(md, ctx=None):
    ctx = ctx or {}
    lines = md.splitlines()
    out, i = [], 0

    def list_block(i, indent):
        tag = "ol" if re.match(r"\s*\d+\.\s", lines[i]) else "ul"
        items = []
        while i < len(lines):
            m = re.match(r"(\s*)(?:[-*]|\d+\.)\s+(.*)$", lines[i])
            if not m or len(m.group(1)) < indent:
                break
            if len(m.group(1)) > indent:
                sub, i = list_block(i, len(m.group(1)))
                items[-1] += sub
                continue
            items.append(_inline(m.group(2), ctx))
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"\s*(?:[-*]|\d+\.)\s", lines[i]) and lines[i].startswith(" " * (indent + 2)):
                items[-1] += " " + _inline(lines[i].strip(), ctx)
                i += 1
        return f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>", i

    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.strip().startswith("<!--"):
            i += 1
        elif re.match(r"\s*(?:[-*]|\d+\.)\s", ln):
            h, i = list_block(i, len(ln) - len(ln.lstrip()))
            out.append(h)
        elif ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            out.append('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{_inline(c, ctx)}</th>" for c in head) +
                       "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{_inline(c, ctx)}</td>" for c in r) + "</tr>" for r in body) +
                       "</tbody></table></div>")
        elif ln.startswith(">"):
            q = []
            while i < len(lines) and lines[i].startswith(">"):
                q.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>" + md_to_html("\n".join(q), ctx) + "</blockquote>")
        else:
            p = []
            while i < len(lines) and lines[i].strip() and not re.match(r"\s*(?:[-*]|\d+\.)\s|\||>", lines[i]):
                p.append(lines[i].strip())
                i += 1
            out.append("<p>" + _inline(" ".join(p), ctx) + "</p>")
    return "".join(out)


def pojmovi_titles(root, predmet, razred):
    """slug → name of every concept page (its `# heading`)."""
    out = {}
    for p in (pathlib.Path(root) / "tools" / predmet / "_source" / f"pojmovi-{razred}").glob("*.md"):
        m = re.search(r"^# (.+)$", p.read_text(encoding="utf-8"), re.M)
        if m:
            out[p.stem] = m.group(1).strip()
    return out

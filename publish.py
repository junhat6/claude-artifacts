#!/usr/bin/env python3
"""Claude Code のアーティファクト HTML をこのリポジトリに取り込み、index.html を再生成する。

使い方:
  python3 publish.py <src.html> [--title "タイトル"] [--slug slug-name]
  python3 publish.py --rebuild        # index.html の再生成のみ

Claude Code の Artifact ツールが書く HTML は <!doctype>/<head>/<body> を持たない
断片なので、そのまま静的配信すると charset や viewport が欠けてモバイル表示が
崩れる。取り込み時に完全な HTML 文書にラップするのはそのため。
"""

import argparse
import datetime
import html
import pathlib
import re
import sys
import unicodedata

REPO = pathlib.Path(__file__).resolve().parent
BASE_URL = "https://junhat6.github.io/claude-artifacts"

# claude.ai がアーティファクト配信時に付ける最小リセットの代替。
# これが無いとアーティファクト側の CSS が前提とする余白ゼロ状態にならない。
RESET_CSS = (
    "*,*::before,*::after{box-sizing:border-box}"
    "body{margin:0;font-family:system-ui,-apple-system,'Hiragino Sans',sans-serif;"
    "line-height:1.6;-webkit-text-size-adjust:100%}"
    "img{max-width:100%}"
)

SKELETON = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{reset}</style>
</head>
<body>
{body}
</body>
</html>
"""


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def extract_title(text: str, fallback: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
    if m and strip_tags(m.group(1)):
        return strip_tags(m.group(1))
    m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S | re.I)
    if m and strip_tags(m.group(1)):
        return strip_tags(m.group(1))
    return fallback


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "artifact"


def wrap_if_fragment(text: str, title: str) -> str:
    if re.match(r"\s*<!doctype", text, re.I):
        return text
    return SKELETON.format(title=html.escape(title), reset=RESET_CSS, body=text)


def unique_dest(name: str) -> pathlib.Path:
    dest = REPO / f"{name}.html"
    n = 2
    while dest.exists():
        dest = REPO / f"{name}-{n}.html"
        n += 1
    return dest


def collect_entries():
    """リポジトリ直下の公開済み HTML から (date, title, filename) を集める。"""
    entries = []
    for p in sorted(REPO.glob("*.html")):
        if p.name == "index.html":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", p.name)
        date = m.group(1) if m else datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()
        title = extract_title(text, p.stem)
        entries.append((date, title, p.name))
    entries.sort(key=lambda e: (e[0], e[2]), reverse=True)
    return entries


def rebuild_index() -> None:
    items = "\n".join(
        f'<li><a href="{html.escape(name)}"><span class="date">{date}</span>'
        f"<span class=\"title\">{html.escape(title)}</span></a></li>"
        for date, title, name in collect_entries()
    ) or '<li class="empty">まだアーティファクトがありません</li>'

    index = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claude Artifacts</title>
<style>
:root {{ --bg:#faf9f7; --fg:#1a1a1a; --muted:#8a8578; --card:#ffffff; --border:#e8e4dc; --accent:#b45309; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#191817; --fg:#eceae6; --muted:#8f8a80; --card:#22211f; --border:#38352f; --accent:#e0a458; }}
}}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--fg);
  font-family:system-ui,-apple-system,'Hiragino Sans',sans-serif; line-height:1.6; }}
main {{ max-width:640px; margin:0 auto; padding:3rem 1.25rem 4rem; }}
h1 {{ font-size:1.4rem; margin:0 0 .25rem; }}
p.sub {{ margin:0 0 2rem; color:var(--muted); font-size:.85rem; }}
ul {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:.5rem; }}
li.empty {{ color:var(--muted); }}
li a {{ display:flex; gap:1rem; align-items:baseline; padding:.8rem 1rem;
  background:var(--card); border:1px solid var(--border); border-radius:10px;
  text-decoration:none; color:inherit; }}
li a:hover {{ border-color:var(--accent); }}
.date {{ color:var(--muted); font-size:.78rem; font-variant-numeric:tabular-nums; flex-shrink:0; }}
.title {{ font-weight:600; }}
</style>
</head>
<body>
<main>
<h1>Claude Artifacts</h1>
<p class="sub">Claude Code が生成したレポート・ドキュメントの保管庫</p>
<ul>
{items}
</ul>
</main>
</body>
</html>
"""
    (REPO / "index.html").write_text(index, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", nargs="?", help="取り込む HTML ファイル")
    ap.add_argument("--title", help="一覧に表示するタイトル（省略時は <title> か <h1> から抽出）")
    ap.add_argument("--slug", help="ファイル名 slug（省略時は元ファイル名から生成）")
    ap.add_argument("--rebuild", action="store_true", help="index.html の再生成のみ行う")
    args = ap.parse_args()

    if args.rebuild:
        rebuild_index()
        print(f"index.html を再生成しました: {BASE_URL}/")
        return

    if not args.src:
        ap.error("src か --rebuild のどちらかを指定してください")

    src = pathlib.Path(args.src).expanduser()
    if not src.is_file():
        sys.exit(f"エラー: ファイルが見つかりません: {src}")

    text = src.read_text(encoding="utf-8", errors="replace")
    title = args.title or extract_title(text, src.stem)
    slug = args.slug or slugify(src.stem)
    date = datetime.date.today().isoformat()

    dest = unique_dest(f"{date}-{slug}")
    dest.write_text(wrap_if_fragment(text, title), encoding="utf-8")
    rebuild_index()

    print(f"取り込み完了: {dest.name}")
    print(f"公開URL: {BASE_URL}/{dest.name}")


if __name__ == "__main__":
    main()

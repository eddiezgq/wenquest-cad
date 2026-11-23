"""Local copy of the WenQuest CAD course pages for the installer (course plan section 13, item 2).

Downloads the live help pages (Chinese and English) and makes them work from disk:
- video posters (jpg) and three.js are copied next to the pages; subtitles (vtt) are inlined (file:// pages cannot read files beside them);
- the videos themselves stay online (about 120 MB): the US learning platform, or the China one when the computer's
  time zone is China;
- the Chinese / English switch links point at index.html.

    python tools/help_offline.py OUT_DIR [BASE_URL]

writes OUT_DIR/wqcad/index.html, OUT_DIR/wqcad/en/index.html and OUT_DIR/wqcad/media/*.jpg.
"""

from __future__ import annotations

import base64
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://learn.wenquestrobotics.com/static/help/wqcad/"
CN_HOST = "learn.wenquestech.online"
US_HOST = "learn.wenquestrobotics.com"

# China time zone: the video addresses switch to the China learning platform before anything is played.
SWITCH = """<script>
(function () {
  var tz = ""; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
  if (!/^Asia\\/(Shanghai|Chongqing|Chungking|Harbin|Urumqi|Kashgar)$|^PRC$/.test(tz)) return;
  document.querySelectorAll("video source").forEach(function (s) { s.src = s.src.replace("%s", "%s"); });
})();
</script>
""" % (US_HOST, CN_HOST)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "wenquest-cad-installer"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def localize(page: str, prefix: str, media_url: str, out_media: Path, cache: dict[str, bytes]) -> str:
    """prefix: how the page refers to media/ ("media/" or "../media/")."""
    p = re.escape(prefix)

    def fetch(name: str) -> bytes:
        if name not in cache:
            cache[name] = get(media_url + name)
        return cache[name]

    def vtt(m):
        return 'src="data:text/vtt;base64,%s"' % base64.b64encode(fetch(m.group(1))).decode()

    def jpg(m):
        name = m.group(2)
        (out_media / name).write_bytes(fetch(name))
        return '%s="%s%s"' % (m.group(1), prefix, name)

    page = re.sub(r'src="%s([^"]+\.vtt)"' % p, vtt, page)
    page = re.sub(r'(poster|src)="%s([^"]+\.(?:jpg|png|webp))"' % p, jpg, page)
    page = re.sub(r'src="%s([^"]+\.mp4)"' % p, lambda m: 'src="%s%s"' % (media_url, m.group(1)), page)
    page = page.replace('href="en/" class="top-other"', 'href="en/index.html" class="top-other"')
    page = page.replace('href="../" class="top-other"', 'href="../index.html" class="top-other"')
    return page.replace("</body>", SWITCH + "</body>")


def main(out: Path, base: str = BASE) -> None:
    base = base.rstrip("/") + "/"
    root = out / "wqcad"
    (root / "en").mkdir(parents=True, exist_ok=True)
    (root / "media").mkdir(parents=True, exist_ok=True)
    cache: dict[str, bytes] = {}
    media_url = base + "media/"
    for rel, prefix in (("index.html", "media/"), ("en/index.html", "../media/")):
        page = get(base + rel).decode("utf-8")
        page = localize(page, prefix, media_url, root / "media", cache)
        left = re.findall(r'(?:src|poster|href)="(?:\.\./)?media/[^"]+"', page)
        assert not [x for x in left if not x.endswith(('.jpg"', '.png"', '.webp"'))], left[:5]
        (root / rel).write_text(page, encoding="utf-8")
        n = len(re.findall(r"<video", page))
        print(f"{rel}: {n} videos, {len(page) // 1024} KB")
    # scripts the pages load from media/ at run time (three.js for the 3D parts)
    for name in sorted(set(re.findall(r'"media/([\w.-]+\.js)"', (root / "index.html").read_text(encoding="utf-8")))):
        (root / "media" / name).write_bytes(get(media_url + name))
    size = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    print(f"help copy: {size / 1e6:.1f} MB in {root}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), *sys.argv[2:3])

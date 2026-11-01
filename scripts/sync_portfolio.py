"""Regenerate the dynamic parts of README.md from the portfolio's YAML data.

Source of truth: https://github.com/DevBD1/devbd1.github.io (src/data/*.yaml)
Only content between the <!-- PORTFOLIO:<name>:START/END --> markers is replaced.
"""
import re
import sys
import urllib.request
from pathlib import Path

import yaml

BASE = "https://raw.githubusercontent.com/DevBD1/devbd1.github.io/main/src/data/"
README = Path(__file__).resolve().parent.parent / "README.md"
ACTIVE = {"live", "beta", "building"}  # skip archived / paused / planned
LABELS = {"live": "Live", "beta": "Beta", "building": "In development"}


def load(name):
    with urllib.request.urlopen(BASE + name + ".yaml", timeout=30) as r:
        return yaml.safe_load(r.read().decode("utf-8"))


def first_sentence(text):
    text = " ".join(str(text).split())
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text


def bio(profile):
    s = f"**{profile['headline']}** — {profile['tagline']}"
    otw = profile.get("openToWork") or {}
    if otw.get("enabled"):
        s += f"\n\n🟢 **{otw['headline']}:** {otw['detail']}"
    return s


def projects(items):
    rows = ["| Project | What it does | Stack | Status |", "|---|---|---|---|"]
    for p in items:
        if p.get("status") not in ACTIVE:
            continue
        links = p.get("links") or {}
        url = links.get("site") or links.get("store") or links.get("repo")
        title = f"[**{p['title']}**]({url})" if url else f"**{p['title']}**"
        stack = ", ".join(p.get("stack") or []) or p.get("kind", "")
        status = p.get("statusNote") or LABELS[p["status"]]
        rows.append(f"| {title} | {first_sentence(p['summary'])} | {stack} | {status} |")
    return "\n".join(rows)


def skills(groups):
    return "\n".join(f"- **{g['group']}:** " + " · ".join(g['items']) for g in groups)


def replace(text, name, body):
    pat = re.compile(
        rf"(<!-- PORTFOLIO:{name}:START -->).*?(<!-- PORTFOLIO:{name}:END -->)", re.S
    )
    if not pat.search(text):
        sys.exit(f"Missing markers for {name}")
    return pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)


def main():
    text = README.read_text(encoding="utf-8")
    text = replace(text, "bio", bio(load("profile")))
    text = replace(text, "projects", projects(load("projects")))
    text = replace(text, "skills", skills(load("skills")))
    README.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()


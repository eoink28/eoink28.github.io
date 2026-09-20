#!/usr/bin/env python3
"""Fail the build if the site picks up common signs of AI-written text.

Two checks:
  1. Characters: em and en dashes, curly quotes, the ellipsis character and emoji,
     in every text file in the repo.
  2. Wording: phrases that read as machine-written, in the visible text of the HTML pages.

Run from the repo root:  python3 tools/check_writing.py
"""

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SELF = pathlib.Path(__file__).resolve()

TEXT_EXTENSIONS = {".html", ".css", ".js", ".txt", ".xml", ".svg", ".md", ".yml", ".json"}
SKIP_DIRS = {".git", "node_modules"}

BANNED_CHARACTERS = {
    "—": "em dash",
    "–": "en dash",
    "‘": "curly single quote",
    "’": "curly apostrophe",
    "“": "curly double quote",
    "”": "curly double quote",
    "…": "ellipsis character",
}
BANNED_ENTITIES = re.compile(r"&(mdash|ndash|lsquo|rsquo|ldquo|rdquo|hellip|#821[1-2]|#8216|#8217|#822[01]|#8230);", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")

# Sources: Wikipedia "Signs of AI writing" and published 2026 AI word lists.
BANNED_PHRASES = [
    "additionally", "at its core", "beacon", "comprehensive", "crafted", "crucial",
    "cutting-edge", "deep dive", "delve", "dive into", "dynamic", "elevate", "embark",
    "empower", "ever-evolving", "fast-paced", "foster", "furthermore", "game-changer",
    "harness", "here's the thing", "in conclusion", "in today's", "innovative",
    "it is important to note", "it's worth noting", "journey", "landscape", "leverage",
    "meticulous", "moreover", "multifaceted", "navigate", "not just", "not only",
    "passion", "passionate", "picture this", "pivotal", "realm", "revolutionary",
    "robust", "seamless", "showcase", "spearhead", "state-of-the-art", "streamline",
    "synergy", "tapestry", "testament", "thrilled", "transformative", "underscore",
    "unleash", "unlock", "utilise", "utilize", "vibrant", "whether you're", "world-class",
]
PHRASE_PATTERN = re.compile(r"\b(" + "|".join(re.escape(p) for p in BANNED_PHRASES) + r")\b", re.I)


def text_files():
    for path in sorted(ROOT.rglob("*")):
        if path.resolve() == SELF or not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def visible_text(source):
    source = re.sub(r"<(script|style)\b.*?</\1>", " ", source, flags=re.S | re.I)
    source = re.sub(r"<[^>]+>", " ", source)
    return html.unescape(source)


def main():
    problems = []

    for path in text_files():
        rel = path.relative_to(ROOT)
        content = path.read_text(encoding="utf-8")

        for number, line in enumerate(content.splitlines(), start=1):
            for char, name in BANNED_CHARACTERS.items():
                if char in line:
                    problems.append(f"{rel}:{number}: {name}")
            for match in BANNED_ENTITIES.finditer(line):
                problems.append(f"{rel}:{number}: HTML entity {match.group(0)}")
            if EMOJI.search(line):
                problems.append(f"{rel}:{number}: emoji")

        if path.suffix.lower() == ".html" and "tools" not in rel.parts:
            for number, line in enumerate(visible_text(content).splitlines(), start=1):
                for match in PHRASE_PATTERN.finditer(line):
                    problems.append(f"{rel}: phrase \"{match.group(0)}\" in: {line.strip()[:90]}")

    if problems:
        print("Writing check failed:")
        for problem in problems:
            print("  " + problem)
        return 1

    print("Writing check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Check WCAG contrast of the main text/background pairs in static/styles.css,
for both the light theme (:root) and the dark theme ([data-bs-theme="dark"]).

AA needs 4.5:1 for normal text. Exits with status 1 if any pair falls short.

Usage:
    python scripts/check_contrast.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "static", "styles.css")

# (foreground variable, background variable, where it is used)
PAIRS = [
    ("--gt-text", "--gt-bg", "body text"),
    ("--gt-text", "--gt-surface", "text on cards and tables"),
    ("--gt-muted", "--gt-surface", "secondary text on cards"),
    ("--gt-muted", "--gt-bg", "secondary text on the page"),
    ("--gt-muted", "--gt-thead", "table headings"),
    ("--gt-primary", "--gt-surface", "links and outline buttons"),
    ("--gt-primary", "--gt-bg", "links on the page"),
    ("--gt-on-primary", "--gt-primary", "primary button label"),
    ("--gt-on-primary", "--gt-primary-dark", "primary button label (hover)"),
    ("--gt-primary-dark", "--gt-primary-soft", "'fresh' status pill"),
    ("--gt-warning", "--gt-warning-soft", "'expiring' status pill"),
    ("--gt-danger", "--gt-danger-soft", "'expired' status pill"),
    ("--gt-danger", "--gt-surface", "delete buttons and errors"),
    ("--gt-text", "--gt-subtle", "secondary buttons"),
    ("--gt-subtle-text", "--gt-subtle", "category pill"),
    ("--gt-text", "--gt-warning-soft", "use-first cards"),
]


def block_vars(css, selector):
    start = css.index(selector + " {")
    body = css[start:css.index("}", start)]
    return dict(re.findall(r"(--gt-[\w-]+):\s*(#[0-9a-fA-F]{6})", body))


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check(css_text=None):
    """Return [(theme, fg, bg, use, ratio)] for every pair."""
    css_text = css_text or open(CSS, encoding="utf-8").read()
    light = block_vars(css_text, ":root")
    dark = {**light, **block_vars(css_text, '[data-bs-theme="dark"]')}
    rows = []
    for theme, palette in (("light", light), ("dark", dark)):
        for fg, bg, use in PAIRS:
            rows.append((theme, fg, bg, use, round(ratio(palette[fg], palette[bg]), 2)))
    return rows


if __name__ == "__main__":
    failed = False
    for theme, fg, bg, use, r in check():
        flag = "ok " if r >= 4.5 else "LOW"
        failed |= r < 4.5
        print(f"{flag} {theme:<5} {r:>5.2f}:1  {use} ({fg} on {bg})")
    sys.exit(1 if failed else 0)

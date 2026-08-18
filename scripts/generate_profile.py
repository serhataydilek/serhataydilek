#!/usr/bin/env python3
"""Generate sparse, GitHub-native SVG profile statistics from public data."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER = "serhataydilek"
W = 620
FEATURED = [
    ("structurAI", "StructurAI", False),
    ("salescallAI", "SalesMirror", False),
    ("kafeproje", "Istanbul Cafe Discovery", True),
    ("construction_video", "video2sfm", False),
    ("videototext", "Video To Text", False),
]


def request(url, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "serhataydilek-profile"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=30) as response:
        return json.load(response)


def api(path): return request(f"https://api.github.com{path}")


def calendar():
    now = datetime.now(timezone.utc)
    query = """query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){contributionsCollection(from:$from,to:$to){totalCommitContributions totalPullRequestContributions totalPullRequestReviewContributions totalIssueContributions restrictedContributionsCount contributionCalendar{totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}"""
    variables = {"login": USER, "from": (now - timedelta(days=364)).isoformat(), "to": now.isoformat()}
    try:
        data = request("https://api.github.com/graphql", json.dumps({"query": query, "variables": variables}).encode())
        collection = data["data"]["user"]["contributionsCollection"]
        cal = collection["contributionCalendar"]
        days = [day for week in cal["weeks"] for day in week["contributionDays"]]
        return {
            "total": cal["totalContributions"], "days": days,
            "commits": collection["totalCommitContributions"],
            "pull_requests": collection["totalPullRequestContributions"],
            "reviews": collection["totalPullRequestReviewContributions"],
            "issues": collection["totalIssueContributions"],
            "restricted": collection["restrictedContributionsCount"],
        }
    except (KeyError, TypeError, ValueError, urllib.error.URLError, urllib.error.HTTPError):
        return {"total": None, "days": [], "commits": None, "pull_requests": None, "reviews": None, "issues": None, "restricted": None}


def load():
    try:
        user = api(f"/users/{USER}")
        repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner&sort=updated") if not r["fork"] and not r["archived"]]
    except (urllib.error.URLError, urllib.error.HTTPError) as err:
        raise SystemExit(f"GitHub API request failed: {err}") from err
    return user, repos, calendar()


def xml_text(x, y, value, cls="t", size=12, anchor="start", weight="400"):
    return f'<text class="{cls}" x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>'


def svg(height, label, body):
    style = '''<style>
text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}.t{fill:#24292f}.m{fill:#656d76}.a{fill:#15803d;stroke:#15803d}.u{stroke:#d0d7de}.g{stroke:#d0d7de}.f{fill:#d0d7de}.q{fill:#b6e3c6}.r{fill:#1a7f37}
@media (prefers-color-scheme: dark){.t{fill:#f0f6fc}.m{fill:#8b949e}.a{fill:#4ade80;stroke:#4ade80}.u{stroke:#30363d}.g{stroke:#30363d}.f{fill:#30363d}.q{fill:#164b32}.r{fill:#4ade80}}
</style>'''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>{style}{body}</svg>'


def put(name, height, label, body):
    path = ASSETS / name
    value = svg(height, label, body)
    if not path.exists() or path.read_text(encoding="utf-8") != value:
        path.write_text(value, encoding="utf-8")


def heading(name):
    body = xml_text(0, 18, name, "t", 14, weight="400") + '<line class="u" x1="82" y1="13" x2="620" y2="13" stroke-width="1"/>'
    put(f"hd-{name}.svg", 26, name, body)


def weekly(days):
    values = [sum(day["contributionCount"] for day in days[i:i + 7]) for i in range(0, len(days), 7)]
    return values or [0]


def stats(user, days, total):
    values, peak = weekly(days), max(weekly(days)) or 1
    base, top = 137, 93
    points = [(i * W / max(len(values) - 1, 1), base - value / peak * (base - top)) for i, value in enumerate(values)]
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in points)
    grid = ''.join(f'<line class="g" x1="0" y1="{y}" x2="620" y2="{y}" stroke-width="1" stroke-dasharray="2 5"/>' for y in (top, (top + base) / 2, base))
    total_label = f"{total} contributions in the last year" if total is not None else "public activity overview"
    body = '<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".5s" fill="freeze"/>'
    body += xml_text(0, 49, total if total is not None else "—", "t", 46, weight="400") + xml_text(0, 70, total_label, "m", 11)
    body += xml_text(620, 30, user.get("public_repos", 0), "a", 18, "end") + xml_text(620, 47, "public repos", "m", 10, "end")
    body += xml_text(620, 67, user.get("followers", 0), "a", 18, "end") + xml_text(620, 84, "followers", "m", 10, "end") + '</g>' + grid
    body += f'<path d="{path}" fill="none" class="a" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"><animate attributeName="stroke-dashoffset" from="1" to="0" dur="1.1s" fill="freeze"/></path>'
    put("stats.svg", 148, "Contribution overview", body)


def about():
    rows = ["Serhat Aydilek", "Computer Engineering student", "Istanbul, Türkiye", "", "İSTÜN", "42 Istanbul", "", "C · C++ · Python · TypeScript", "AI · software · systems · computer vision"]
    body = ''.join(xml_text(0, 19 + i * 17, value, "t" if i in (0, 4, 5) else "m", 12 if i != 0 else 14, weight="400") for i, value in enumerate(rows) if value)
    put("about.svg", 161, "About Serhat Aydilek", body)


def repo_panel(repos):
    indexed = {repo["name"]: repo for repo in repos}
    body = ''
    for i, (slug, name, active) in enumerate(FEATURED):
        repo, y = indexed.get(slug), 20 + i * 30
        language = repo.get("language") if repo else None
        updated = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00")).strftime("%b %Y").lower() if repo else "unpublished"
        right = "Flutter · currently building" if active else (language or "repository")
        body += xml_text(0, y, f"{i + 1:02d}", "m", 10) + xml_text(31, y, name, "t", 12) + xml_text(620, y, right, "a" if active else "m", 11, "end")
        body += xml_text(31, y + 14, f"updated {updated}", "m", 10)
        if i < len(FEATURED) - 1: body += f'<line class="u" x1="31" y1="{y + 21}" x2="620" y2="{y + 21}" stroke-width="1"/>'
    put("repos.svg", 166, "Featured projects", body)


def social(user, repos):
    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    cells = [(user.get("followers", 0), "followers"), (user.get("following", 0), "following"), (stars, "stars earned")]
    body = ''
    for i, (value, label) in enumerate(cells):
        x = i * 206
        body += xml_text(x, 31, value, "a", 21) + xml_text(x, 49, label, "m", 10)
    body += '<line class="u" x1="0" y1="66" x2="620" y2="66" stroke-width="1"/>'
    body += xml_text(0, 91, "linkedin", "m", 11) + xml_text(90, 91, "serhat-aydilek-a50873371", "t", 11)
    body += xml_text(0, 111, "email", "m", 11) + xml_text(90, 111, "serhat.aydilek.dev@gmail.com", "t", 11)
    put("social.svg", 127, "Social links and GitHub counts", body)


def activity(metrics):
    kinds = [("commits", "commits · last 365d"), ("pull_requests", "pull requests · last 365d"), ("reviews", "reviews · last 365d"), ("issues", "issues · last 365d")]
    available = all(metrics[key] is not None for key, _ in kinds)
    values = [metrics[key] or 0 for key, _ in kinds]
    peak = max(values) or 1
    body = xml_text(0, 16, "last 365 days" if available else "last 365 days · yearly categories unavailable", "m", 10)
    for i, ((key, label), value) in enumerate(zip(kinds, values)):
        y = 37 + i * 22
        body += xml_text(0, y, label, "m", 11) + f'<line class="u" x1="180" y1="{y - 4}" x2="550" y2="{y - 4}" stroke-width="2"/>'
        if available:
            body += f'<line class="a" x1="180" y1="{y - 4}" x2="{180 + 370 * value / peak:.1f}" y2="{y - 4}" stroke="currentColor" stroke-width="2"><animate attributeName="x2" from="180" to="{180 + 370 * value / peak:.1f}" dur=".6s" fill="freeze"/></line>'
        body += xml_text(620, y, value if available else "—", "t", 11, "end")
    put("activity.svg", 130, "GitHub contribution activity over the last 365 days", body)


def streak(days):
    values = [day["contributionCount"] for day in days]
    longest = run = 0
    for value in values:
        run = run + 1 if value else 0; longest = max(longest, run)
    current = 0
    for value in reversed(values):
        if not value: break
        current += 1
    body = xml_text(0, 29, current, "a", 25) + xml_text(0, 48, "current active-day streak", "m", 10)
    body += xml_text(310, 29, longest, "a", 25) + xml_text(310, 48, "longest active-day streak", "m", 10)
    body += xml_text(620, 48, "calendar year", "m", 10, "end")
    put("streak.svg", 64, "Contribution streaks", body)


def langs(repos):
    totals, repo_counts = Counter(), Counter()
    for repo in repos:
        if repo["name"].lower() == USER: continue
        try:
            languages = api(f"/repos/{USER}/{repo['name']}/languages")
        except (urllib.error.URLError, urllib.error.HTTPError):
            continue
        totals.update(languages)
        repo_counts.update(languages.keys())
    total = sum(totals.values()) or 1
    top = totals.most_common(5)
    x, body = 0, xml_text(0, 16, "top languages by GitHub Linguist bytes", "m", 10)
    for i, (_, value) in enumerate(top):
        width = value / total * W
        body += f'<rect x="{x:.1f}" y="28" width="{width:.1f}" height="5" class="{"r" if i == 0 else "q"}"/>'; x += width
    for i, (name, value) in enumerate(top): body += xml_text(0, 57 + i * 16, f"{name:<16} {value * 100 / total:5.1f}%   {repo_counts[name]} repos", "t" if i == 0 else "m", 11)
    put("langs.svg", 139, "Languages across owned repositories", body)


def weekday(days):
    totals = [0] * 7
    for day in days: totals[day["weekday"]] += day["contributionCount"]
    peak = max(totals) or 1
    body = xml_text(0, 15, "contributions by weekday · monday first", "m", 10)
    for i, day in enumerate([1, 2, 3, 4, 5, 6, 0]):
        x, value = i * 88, totals[day]
        body += xml_text(x, 78, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i], "m", 10)
        body += f'<rect class="f" x="{x}" y="25" width="52" height="42"/><rect class="r" x="{x}" y="{67 - value / peak * 42:.1f}" width="52" height="{value / peak * 42:.1f}"><animate attributeName="height" from="0" to="{value / peak * 42:.1f}" dur=".5s" fill="freeze"/></rect>'
        body += xml_text(x + 52, 18, value, "t", 10, "end")
    put("weekday.svg", 91, "Weekday contribution distribution", body)


def year(days):
    body = xml_text(0, 12, "last 365 days · public contribution calendar", "m", 10)
    for i, day in enumerate(days[-365:]):
        x, y = (i % 73) * 8.45, 29 + (i // 73) * 13
        cls = "r" if day["contributionCount"] >= 4 else "q" if day["contributionCount"] else "m"
        char = "▪" if day["contributionCount"] else "·"
        body += xml_text(x, y, char, cls, 11)
    put("year.svg", 101, "Year contribution rhythm", body)


def main():
    ASSETS.mkdir(exist_ok=True)
    user, owned_repos, metrics = load()
    stats(user, metrics["days"], metrics["total"])
    for name in ("about", "projects", "social", "activity", "stats"): heading(name)
    about(); repo_panel(owned_repos); social(user, owned_repos); activity(metrics); streak(metrics["days"]); langs(owned_repos); weekday(metrics["days"]); year(metrics["days"])
    print(f"generated minimal profile assets from {len(owned_repos)} owned public repositories")


if __name__ == "__main__": main()

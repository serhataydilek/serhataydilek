#!/usr/bin/env python3
"""Generate the SVG panels used by this GitHub profile README."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER = "serhataydilek"
WIDTH = 744
FEATURED = [
    ("structurAI", "StructurAI", None, False),
    ("salescallAI", "SalesMirror", None, False),
    ("kafeproje", "Istanbul Cafe Discovery", "Discover cafés around Istanbul through a map-focused discovery experience.", True),
    ("construction_video", "video2sfm", None, False),
    ("videototext", "Video To Text", None, False),
]

def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "serhataydilek-profile-generator"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token: headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response: return json.load(response)

def fetch():
    try:
        user = api(f"/users/{USER}")
        repos = api(f"/users/{USER}/repos?per_page=100&type=owner&sort=updated")
        events = api(f"/users/{USER}/events/public?per_page=100")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
        raise SystemExit(f"GitHub API request failed: {err}") from err
    return user, [r for r in repos if not r["fork"] and not r["archived"]], events

def date(value): return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %b %Y").lower()
def short(value, limit):
    value = " ".join((value or "").split())
    return value if len(value) <= limit else value[:limit - 1].rstrip() + "…"
def t(x, y, value, cls="text", size=13, weight="normal", anchor="start"):
    return f'<text class="{cls}" x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>'
def document(height, label, body):
    style = '''<style>.canvas{fill:#f8fafc}.card{fill:#fff;stroke:#cbd5e1}.line{stroke:#d7e0df}.muted{fill:#52606d}.text{fill:#16221d}.accent{fill:#15803d}.dim{fill:#6b7a73}.bar{fill:#bbf7d0}.fill{fill:#16a34a}.spark{stroke:#16a34a}.grid{stroke:#d9e5df}text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,Liberation Mono,monospace}@media (prefers-color-scheme: dark){.canvas{fill:#07110c}.card{fill:#0b1710;stroke:#254735}.line{stroke:#20392b}.muted{fill:#91a89a}.text{fill:#e5f5eb}.accent{fill:#4ade80}.dim{fill:#6f8a79}.bar{fill:#17452a}.fill{fill:#4ade80}.spark{stroke:#4ade80}.grid{stroke:#163021}}</style>'''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>{style}<rect class="canvas" width="100%" height="100%" rx="12"/><rect class="card" x="1" y="1" width="{WIDTH-2}" height="{height-2}" rx="11"/>{body}</svg>'
def head(title, right="~/serhat"):
    return t(28,34,f"{title} /","accent",12,"bold")+t(716,34,right,"dim",11,anchor="end")+'<line class="line" x1="28" y1="48" x2="716" y2="48"/>'
def save(name, height, label, body): (ASSETS/name).write_text(document(height,label,body),encoding="utf-8")

def hero():
    cube='''<g transform="translate(620 106)" fill="none" class="spark" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><g><animateTransform attributeName="transform" type="rotate" values="0;10;0;-10;0" dur="10s" repeatCount="indefinite"/><path d="M-42 -18 L0 -40 L42 -18 L0 4 Z" opacity=".35"/><path d="M-46 12 L-4 -10 L38 12 L-4 34 Z"/><path d="M-42 -18 L-46 12 M0 -40 L-4 -10 M42 -18 L38 12 M0 4 L-4 34" opacity=".7"/></g><g class="fill"><circle cx="-50" cy="-38" r="2"><animate attributeName="opacity" values=".2;1;.2" dur="3s" repeatCount="indefinite"/></circle><circle cx="50" cy="36" r="2"><animate attributeName="opacity" values="1;.2;1" dur="3.7s" repeatCount="indefinite"/></circle><circle cx="31" cy="-47" r="1.5"/></g></g>'''
    body=head("serhat@github:~$")+t(28,94,"SERHAT AYDILEK","text",29,"bold")+t(28,124,"computer engineering  ·  software  ·  ai  ·  systems","muted",13)+t(28,156,"istanbul, tr","accent",12,"bold")+t(28,188,"building practical products at the intersection of code and curiosity","dim",12)+cube+'<rect class="fill" x="28" y="211" width="8" height="14"><animate attributeName="opacity" values="1;0;1" dur="1.1s" repeatCount="indefinite"/></rect>'
    save("hero.svg",232,"Serhat Aydilek developer dashboard",body)

def about():
    body=head("about")
    for i,(key,value) in enumerate([("location","istanbul, tr"),("education","computer engineering · İSTÜN"),("currently","42 istanbul"),("focus","software · ai · systems · computer vision")]):
        y=80+i*27; body+=t(28,y,key.ljust(12),"dim",12)+t(174,y,value,"text",12)
    x=28
    for tag in ["C","C++","Python","TypeScript","React","FastAPI","Git","AWS"]:
        w=18+len(tag)*7; body+=f'<rect class="bar" x="{x}" y="205" width="{w}" height="25" rx="4"/>'+t(x+w/2,222,tag,"accent",11,"bold","middle"); x+=w+8
    save("about.svg",252,"About Serhat Aydilek",body)

def projects(repos):
    by_name={r["name"]:r for r in repos}; body=head("featured projects","git log --focus")
    for i,(name,display,preferred_description,active) in enumerate(FEATURED):
        y=76+i*62; repo=by_name.get(name)
        if repo:
            language=repo.get("language") or "repository"; metric=f"★ {repo['stargazers_count']}" if repo.get("stargazers_count") else f"updated {date(repo['updated_at'])}"; description=short(preferred_description or repo.get("description") or "Project details available on GitHub.",76)
        else: language,metric,description="repository","","Repository currently unavailable."
        status="currently building" if active else language.lower()
        body+=t(28,y,f"0{i+1}","accent",11,"bold")+t(68,y,display,"text",14,"bold")+t(716,y,metric,"dim",11,anchor="end")+t(68,y+20,description,"muted",11)+t(68,y+39,status,"accent",11,"bold" if active else "normal")
        if i<4: body+=f'<line class="line" x1="28" y1="{y+50}" x2="716" y2="{y+50}"/>'
    save("projects.svg",398,"Featured GitHub projects",body)

def activity(user,repos,events):
    pushes=[e for e in events if e.get("type")=="PushEvent"]; recent=[]
    for e in pushes:
        name=e.get("repo",{}).get("name","").split("/")[-1]
        if name and name not in recent: recent.append(name)
    body=head("public activity","api / public data")
    for i,(label,value) in enumerate([("public repos",user.get("public_repos",0)),("followers",user.get("followers",0)),("stars earned",sum(r.get("stargazers_count",0) for r in repos)),("recent pushes",len(pushes))]):
        x=28+i*172; body+=t(x,88,value,"accent",25,"bold")+t(x,110,label,"muted",11)
    body+='<line class="line" x1="28" y1="133" x2="716" y2="133"/>'+t(28,162,"recent repository rhythm","dim",11,"bold")+t(28,185,short(" · ".join(recent[:4]) if recent else "no recent public push events returned",95),"text",12)
    save("activity.svg",210,"Public GitHub activity",body)

def languages(repos):
    totals=Counter()
    for repo in repos:
        if repo["name"].lower()==USER: continue
        try: totals.update(api(f"/repos/{USER}/{repo['name']}/languages"))
        except (urllib.error.URLError,urllib.error.HTTPError): pass
    ranking=totals.most_common(5); total=sum(totals.values()) or 1; body=head("language signal","owned public repositories"); x=28; colors=["#4ade80","#22c55e","#16a34a","#15803d","#166534"]
    for i,(_,amount) in enumerate(ranking):
        w=round(688*amount/total); body+=f'<rect x="{x}" y="72" width="{w}" height="15" fill="{colors[i]}" rx="2"/>'; x+=w
    x=28
    for i,(lang,amount) in enumerate(ranking): body+=f'<circle cx="{x+4}" cy="121" r="4" fill="{colors[i]}"/>'+t(x+14,125,f"{lang} {round(amount*100/total)}%","muted",11); x+=132
    body+=t(28,161,"computed from GitHub Linguist byte counts; profile assets excluded","dim",10); save("languages.svg",184,"Language signal across owned public repositories",body)

def streak(events):
    by_day=Counter(e.get("created_at","")[:10] for e in events if e.get("created_at")); values=list(by_day.values())[:28]; body=head("development pulse","last public events")
    for i in range(28):
        value=values[i] if i<len(values) else 0; opacity=min(.95,.18+value*.18) if value else .08; x,y=29+(i%14)*49,70+(i//14)*28; body+=f'<rect class="fill" x="{x}" y="{y}" width="31" height="16" rx="3" opacity="{opacity}">'+('<animate attributeName="opacity" values=".35;.95;.35" dur="5s" repeatCount="indefinite"/>' if value else '')+'</rect>'
    body+=t(28,150,"a lightweight rhythm view from GitHub public event data","dim",10); save("streak.svg",174,"Recent public development rhythm",body)

def footer():
    body=t(28,42,"serhat@github:~$","accent",12,"bold")+t(156,42,"keep building · keep learning","muted",12)+'<g transform="translate(681 33)" class="accent"><path d="M0-9a9 9 0 1 0 5 16A8 8 0 1 1 0-9z"/><path d="M12-3l1.7 3.6 3.8.5-2.8 2.7.7 3.8-3.4-1.9-3.4 1.9.7-3.8-2.8-2.7 3.8-.5z"/></g>'
    save("footer.svg",66,"Profile footer",body)

def main():
    ASSETS.mkdir(exist_ok=True); user,repos,events=fetch(); hero(); about(); projects(repos); activity(user,repos,events); languages(repos); streak(events); footer(); print(f"Generated profile SVGs for {USER}: {len(repos)} public owned repositories.")
if __name__=="__main__": main()

#!/usr/bin/env python3
"""Render a monochrome glass contribution graph as assets/contributions.svg.

Runs in GitHub Actions (see .github/workflows/contributions.yml). It reads the
contribution calendar from the GitHub GraphQL API, so the graph and stats stay
in sync with your real activity. Standard library only.

  GH_TOKEN=... python scripts/contributions.py --user pabilandokarenpv
  python scripts/contributions.py --sample      # offline preview data
"""
import argparse, datetime as dt, json, os, random, urllib.request

QUERY = """query($login:String!){user(login:$login){contributionsCollection{
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-graph"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"], LEVEL[d["contributionLevel"]]) for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def sample():
    rnd = random.Random(1927)
    start = dt.date(2025, 11, 9) - dt.timedelta(days=dt.date(2025, 11, 9).weekday() + 1)
    days = []
    for i in range(53 * 7):
        d = start + dt.timedelta(days=i)
        w = i // 7
        p = .75 if 8 <= w <= 12 else .5 if w <= 17 and w > 12 else .8 if 18 <= w <= 28 else .55 if 38 <= w <= 44 else .14
        c = 0
        if rnd.random() < p:
            c = rnd.choice([1, 2, 3, 5, 8, 11, 15, 24])
        days.append((d.isoformat(), c, 0 if c == 0 else 1 if c < 3 else 2 if c < 6 else 3 if c < 12 else 4))
    days[-1] = (days[-1][0], 5, 2); days[-2] = (days[-2][0], 3, 1); days[-3] = (days[-3][0], 8, 3)
    return sum(c for _, c, _ in days), days


def streaks(days):
    best = run = 0
    for _, c, _ in days:
        run = run + 1 if c else 0
        best = max(best, run)
    counts = [c for _, c, _ in days]
    if counts and counts[-1] == 0:   # today may not have activity yet
        counts = counts[:-1]
    cur = 0
    for c in reversed(counts):
        if not c:
            break
        cur += 1
    return cur, best


def render(total, days, note):
    cell, gap, x0, y0 = 11, 3, 62, 118
    fills = ["#ffffff0d", "#ffffff38", "#ffffff70", "url(#l3)", "#ffffff"]
    rects, months, last_m = [], [], None
    for i, (date, count, lvl) in enumerate(days):
        w, d = divmod(i, 7)
        x, y = x0 + w * (cell + gap), y0 + d * (cell + gap)
        glow = ' filter="url(#glow)"' if lvl == 4 else ""
        delay = f"{(w * 0.035):.2f}"
        rects.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{fills[lvl]}"{glow} style="animation-delay:{delay}s"><title>{count} on {date}</title></rect>')
        m = date[5:7]
        if d == 0 and m != last_m:
            last_m = m
            if w < 52:
                months.append(f'<text x="{x}" y="{y0 - 10}" class="m">{dt.date.fromisoformat(date).strftime("%b")}</text>')
    cur, best = streaks(days)
    busiest = max(days, key=lambda t: t[1])
    active = sum(1 for _, c, _ in days if c)
    stats = [(f"{total:,}", "contributions"), (f"{cur} days", "current streak"), (f"{best} days", "longest streak"), (f"{active}", "active days")]
    boxes = []
    for i, (v, k) in enumerate(stats):
        bx = 30 + i * 197
        boxes.append(f'<rect x="{bx}" y="252" width="185" height="70" rx="14" fill="#ffffff08" stroke="#ffffff17"/>'
                     f'<text x="{bx + 16}" y="284" class="v">{v}</text><text x="{bx + 16}" y="306" class="k">{k}</text>')
    W, H = 840, 350
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total:,} contributions in the last year">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1b1b1d"/><stop offset=".45" stop-color="#0b0b0c"/><stop offset="1" stop-color="#060606"/></linearGradient>
<linearGradient id="l3" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f2f2f3"/><stop offset="1" stop-color="#9d9da2"/></linearGradient>
<linearGradient id="chrome" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset=".5" stop-color="#d0d0d4"/><stop offset=".56" stop-color="#8a8a90"/><stop offset="1" stop-color="#e8e8ea"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".08"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<filter id="glow" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="card"><rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22"/></clipPath>
</defs>
<style>
text{{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",Helvetica,Arial,sans-serif;fill:#f2f2f3}}
.lbl{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:11px;letter-spacing:.14em;fill:#a1a1a6}}
.m,.d{{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:10.5px;fill:#8e8e93}}
.h{{font-size:26px;font-weight:500;letter-spacing:-.4px}}
.v{{font-size:22px;font-weight:500}}.k{{font-size:12px;fill:#8e8e93}}
.note{{font-size:11.5px;fill:#6e6e73}}
rect[style]{{animation:pulse 9s ease-out infinite}}
@keyframes pulse{{0%,86%,100%{{opacity:1}}90%{{opacity:.45}}}}
.sweep{{animation:sweep 8s ease-in-out infinite}}
@keyframes sweep{{0%,60%{{transform:translateX(-900px)}}90%,100%{{transform:translateX(900px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect class="sweep" x="0" y="0" width="420" height="{H}" fill="url(#sheen)" transform="skewX(-20)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="#ffffff38"/>
<text x="30" y="40" class="lbl">CONTRIBUTION ACTIVITY</text>
<text x="30" y="76" class="h"><tspan fill="url(#chrome)" font-weight="700">{total:,}</tspan> contributions in the last year</text>
<text x="810" y="40" class="note" text-anchor="end">{note}</text>
{''.join(months)}
<text x="30" y="{y0 + 1 * 14 + 9}" class="d">Mon</text><text x="30" y="{y0 + 3 * 14 + 9}" class="d">Wed</text><text x="30" y="{y0 + 5 * 14 + 9}" class="d">Fri</text>
{''.join(rects)}
{''.join(boxes)}
</svg>'''


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "pabilandokarenpv"))
    ap.add_argument("--out", default="assets/contributions.svg")
    ap.add_argument("--sample", action="store_true")
    a = ap.parse_args()
    if a.sample:
        total, days = sample()
        note = "Sample data · real graph updates every 6 hours"
    else:
        total, days = fetch(a.user, os.environ["GH_TOKEN"])
        note = "Updated " + dt.datetime.utcnow().strftime("%b %d, %Y · %H:%M UTC")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write(render(total, days[-371:], note))
    print(f"wrote {a.out}: {total} contributions")

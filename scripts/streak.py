# Builds streak.svg from the contribution calendar, private contributions included when the token allows.
import json, os, urllib.request
from datetime import date, timedelta

USER, TOKEN = os.environ["USERNAME"], os.environ["GITHUB_TOKEN"]

def gql(q):
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": q}).encode(),
                                 {"Authorization": f"bearer {TOKEN}"})
    return json.load(urllib.request.urlopen(req))["data"]["user"]

years = gql(f'{{user(login:"{USER}"){{contributionsCollection{{contributionYears}}}}}}')["contributionsCollection"]["contributionYears"]
days = {}
for y in years:
    cal = gql(f'{{user(login:"{USER}"){{contributionsCollection(from:"{y}-01-01T00:00:00Z",to:"{y}-12-31T23:59:59Z")'
              '{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}')
    for w in cal["contributionsCollection"]["contributionCalendar"]["weeks"]:
        for d in w["contributionDays"]:
            days[date.fromisoformat(d["date"])] = d["contributionCount"]

today = date.today()
days = {d: c for d, c in days.items() if d <= today}
active = sorted(d for d, c in days.items() if c)
total, first = sum(days.values()), active[0]

# longest run of consecutive active days
best = (0, first, first); run_start = prev = None
for d in active:
    run_start = d if prev is None or d - prev > timedelta(1) else run_start
    if (d - run_start).days + 1 > best[0]: best = ((d - run_start).days + 1, run_start, d)
    prev = d

# current streak: today may still be empty, so start from yesterday in that case
d = today if days.get(today) else today - timedelta(1)
end, cur = d, 0
while days.get(d):
    cur += 1; d -= timedelta(1)
cur_range = (d + timedelta(1), end)

fmt = lambda x: f"{x:%b} {x.day}, {x.year}"
short = lambda x: f"{x:%b} {x.day}"
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" font-family="Segoe UI,Ubuntu,sans-serif">
<rect width="495" height="195" rx="4.5" fill="#0d1117"/>
<line x1="165" y1="28" x2="165" y2="170" stroke="#e4e2e2" stroke-width="1"/>
<line x1="330" y1="28" x2="330" y2="170" stroke="#e4e2e2" stroke-width="1"/>
<g text-anchor="middle">
<text x="82.5" y="79" fill="#70a5fd" font-size="28" font-weight="700">{total:,}</text>
<text x="82.5" y="116" fill="#70a5fd" font-size="14">Total Contributions</text>
<text x="82.5" y="145" fill="#38bdae" font-size="12">{fmt(first)} - Present</text>
<circle cx="247.5" cy="71" r="40" fill="none" stroke="#70a5fd" stroke-width="5"/>
<text x="247.5" y="80" fill="#bf91f3" font-size="28" font-weight="700">{cur}</text>
<text x="247.5" y="140" fill="#bf91f3" font-size="14" font-weight="700">Current Streak</text>
<text x="247.5" y="165" fill="#38bdae" font-size="12">{(short(cur_range[0]) + " - " + short(cur_range[1])) if cur else "Start one today"}</text>
<text x="412.5" y="79" fill="#70a5fd" font-size="28" font-weight="700">{best[0]}</text>
<text x="412.5" y="116" fill="#70a5fd" font-size="14">Longest Streak</text>
<text x="412.5" y="145" fill="#38bdae" font-size="12">{short(best[1])}, {best[1].year} - {short(best[2])}, {best[2].year}</text>
</g></svg>'''
open("streak.svg", "w").write(svg)
print(total, cur, best)

#!/usr/bin/env python3
"""
sleep_dashboard.py — Read a sleep-tracking CSV and generate an HTML dashboard
about overall sleep health.

CSV format (header may contain spaces after commas):
    sleep_date, begin_hhmm, end_hhmm
    2026-07-02,0115,0915

Each row's `sleep_date` is the morning you woke. `begin_hhmm` is the clock time
you fell asleep, `end_hhmm` the clock time you woke. If begin > end, the sleep
crossed midnight and started the previous calendar day. Missing nights (equipment
failure) simply have no row and are handled gracefully.

Usage:
    python sleep_dashboard.py [path/to/sleep.csv] [-o dashboard.html]
Defaults: input "sleep.csv" in the current directory, output "sleep_dashboard.html".
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Font stack used throughout the dashboard. Customise freely; the first
# available family wins, falling back rightward.
FONT_STACK = "'Andika','Iowan Old Style','Palatino Linotype',Georgia,serif"


# --------------------------------------------------------------------------- #
# Data model & parsing
# --------------------------------------------------------------------------- #

@dataclass
class Night:
    wake_date: dt.date          # the morning you woke (= sleep_date column)
    start: dt.datetime          # full datetime sleep began
    end: dt.datetime            # full datetime sleep ended
    duration_h: float           # hours asleep


def _parse_hhmm(value: str) -> dt.time:
    """Parse 'HHMM' (e.g. '0130' or '2330'). Also tolerates 'H:MM'/'HH:MM'."""
    v = value.strip().replace(":", "")
    if not v.isdigit() or len(v) > 4:
        raise ValueError(f"bad time {value!r}")
    v = v.zfill(4)
    h, m = int(v[:2]), int(v[2:])
    if h > 23 or m > 59:
        raise ValueError(f"time out of range {value!r}")
    return dt.time(h, m)


def load_nights(path: str) -> tuple[list[Night], list[str]]:
    """Read the CSV, return (nights sorted by date, list of warning strings)."""
    nights: list[Night] = []
    warnings: list[str] = []

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise SystemExit(f"'{path}' is empty.")
        # Normalise header names (strip whitespace) to find columns robustly.
        cols = {name.strip().lower(): i for i, name in enumerate(header)}
        try:
            i_date = cols["sleep_date"]
            i_begin = cols["begin_hhmm"]
            i_end = cols["end_hhmm"]
        except KeyError:
            # Fall back to positional order if header names differ.
            i_date, i_begin, i_end = 0, 1, 2
            warnings.append("Header not recognised; assumed columns date,begin,end.")

        for lineno, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue  # blank line
            try:
                wake_date = dt.date.fromisoformat(row[i_date].strip())
                t_begin = _parse_hhmm(row[i_begin])
                t_end = _parse_hhmm(row[i_end])
            except (ValueError, IndexError) as exc:
                warnings.append(f"Line {lineno}: skipped ({exc}).")
                continue

            end_dt = dt.datetime.combine(wake_date, t_end)
            # If begin time is later in the clock than end time, sleep began the
            # previous calendar day (crossed midnight).
            if t_begin > t_end:
                start_dt = dt.datetime.combine(
                    wake_date - dt.timedelta(days=1), t_begin
                )
            else:
                start_dt = dt.datetime.combine(wake_date, t_begin)

            duration_h = (end_dt - start_dt).total_seconds() / 3600.0
            if not (0 < duration_h <= 24):
                warnings.append(
                    f"Line {lineno}: implausible duration {duration_h:.1f}h, skipped."
                )
                continue

            nights.append(Night(wake_date, start_dt, end_dt, duration_h))

    nights.sort(key=lambda n: n.wake_date)
    # Deduplicate by wake_date (keep last).
    seen: dict[dt.date, Night] = {}
    for n in nights:
        seen[n.wake_date] = n
    return list(seen.values()), warnings


# --------------------------------------------------------------------------- #
# Analytics
# --------------------------------------------------------------------------- #

def _minutes_since_noon(t: dt.datetime) -> float:
    """Clock time expressed as minutes since noon, so late-night bedtimes
    (e.g. 01:00) sort naturally after evening ones (e.g. 23:00)."""
    m = t.hour * 60 + t.minute
    ref = m - 12 * 60
    if ref < 0:
        ref += 24 * 60
    return ref


def _fmt_clock_from_noon(minutes: float) -> str:
    total = int(round(minutes)) + 12 * 60
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def _fmt_hm(hours: float) -> str:
    h = int(hours)
    m = int(round((hours - h) * 60))
    if m == 60:
        h, m = h + 1, 0
    return f"{h}h {m:02d}m"


def _weekly_series(nights: list[Night], weeks_back: int = 8) -> list[dict]:
    """Aggregate nights into ISO weeks, returning the last `weeks_back` weeks
    (chronological). Each entry carries both mean and median bedtime/waketime
    (as minutes-since-noon and formatted clock strings) plus the derived
    duration for each aggregation."""
    by_week: dict[tuple[int, int], list[Night]] = defaultdict(list)
    for n in nights:
        iso = n.wake_date.isocalendar()
        by_week[(iso[0], iso[1])].append(n)

    keys = sorted(by_week)[-weeks_back:]
    out: list[dict] = []
    for (yr, wk) in keys:
        group = by_week[(yr, wk)]
        beds = [_minutes_since_noon(n.start) for n in group]
        durs = [n.duration_h for n in group]  # minutes below

        mean_bed = statistics.mean(beds)
        med_bed = statistics.median(beds)
        mean_dur_min = statistics.mean(durs) * 60
        med_dur_min = statistics.median(durs) * 60

        # Monday date of the ISO week, for the axis label.
        monday = dt.date.fromisocalendar(yr, wk, 1)

        out.append({
            "label": monday.isoformat()[5:],   # MM-DD of week start
            "week": f"{yr}-W{wk:02d}",
            "nights": len(group),
            # Means
            "mean_bed_min": round(mean_bed, 1),
            "mean_wake_min": round(mean_bed + mean_dur_min, 1),
            "mean_dur": round(mean_dur_min / 60, 2),
            "mean_bed": _fmt_clock_from_noon(mean_bed),
            "mean_wake": _fmt_clock_from_noon(mean_bed + mean_dur_min),
            # Medians
            "med_bed_min": round(med_bed, 1),
            "med_wake_min": round(med_bed + med_dur_min, 1),
            "med_dur": round(med_dur_min / 60, 2),
            "med_bed": _fmt_clock_from_noon(med_bed),
            "med_wake": _fmt_clock_from_noon(med_bed + med_dur_min),
        })
    return out


def analyse(nights: list[Night]) -> dict:
    if not nights:
        raise SystemExit("No valid sleep records found.")

    durations = [n.duration_h for n in nights]
    span_days = (nights[-1].wake_date - nights[0].wake_date).days + 1
    recorded = len(nights)

    # Regularity: stdev of bedtime and wake time (minutes-since-noon frame).
    bed_mins = [_minutes_since_noon(n.start) for n in nights]
    wake_mins = [_minutes_since_noon(n.end) for n in nights]
    bed_sd = statistics.pstdev(bed_mins) if len(bed_mins) > 1 else 0.0
    wake_sd = statistics.pstdev(wake_mins) if len(wake_mins) > 1 else 0.0

    # A simple sleep-health score (0-100) built from three components:
    #   duration adequacy, duration consistency, and schedule regularity.
    avg = statistics.mean(durations)
    dur_sd = statistics.pstdev(durations) if len(durations) > 1 else 0.0

    def clamp(x, lo=0.0, hi=1.0):
        return max(lo, min(hi, x))

    # Duration score: full marks for 7-9h, tapering outside.
    if 7 <= avg <= 9:
        dur_score = 1.0
    elif avg < 7:
        dur_score = clamp(1 - (7 - avg) / 3)      # 0 at ~4h
    else:
        dur_score = clamp(1 - (avg - 9) / 3)      # 0 at ~12h

    # Consistency score: smaller night-to-night duration swing is better.
    cons_score = clamp(1 - dur_sd / 2.0)          # 0 when sd >= 2h

    # Regularity score: smaller bedtime swing is better.
    reg_score = clamp(1 - bed_sd / 120.0)         # 0 when sd >= 2h

    score = round(100 * (0.5 * dur_score + 0.25 * cons_score + 0.25 * reg_score))

    # Distribution buckets.
    buckets = {"<5h": 0, "5–6h": 0, "6–7h": 0, "7–8h": 0, "8–9h": 0, "9h+": 0}
    for d in durations:
        if d < 5:
            buckets["<5h"] += 1
        elif d < 6:
            buckets["5–6h"] += 1
        elif d < 7:
            buckets["6–7h"] += 1
        elif d < 8:
            buckets["7–8h"] += 1
        elif d < 9:
            buckets["8–9h"] += 1
        else:
            buckets["9h+"] += 1

    # Weekday averages (0=Mon).
    by_wd = defaultdict(list)
    for n in nights:
        by_wd[n.wake_date.weekday()].append(n.duration_h)
    weekday_avg = [
        round(statistics.mean(by_wd[i]), 2) if by_wd[i] else None
        for i in range(7)
    ]

    # 7-night rolling average of duration, for the trend line.
    series = []
    window: list[float] = []
    for n in nights:
        window.append(n.duration_h)
        if len(window) > 7:
            window.pop(0)
        bed_m = _minutes_since_noon(n.start)
        wake_m = _minutes_since_noon(n.end)
        series.append(
            {
                "date": n.wake_date.isoformat(),
                "duration": round(n.duration_h, 2),
                "rolling": round(statistics.mean(window), 2),
                "bed": _fmt_clock_from_noon(bed_m),
                "wake": _fmt_clock_from_noon(bed_m + n.duration_h * 60),
                "bed_min": round(bed_m, 1),
                # End expressed on the same continuous axis as bed_min, so the
                # clock-time bar spans exactly the duration even past midnight.
                "wake_min": round(bed_m + n.duration_h * 60, 1),
            }
        )

    # Weekly aggregations (mean & median) for the last 8 ISO weeks present.
    weekly = _weekly_series(nights, weeks_back=8)

    return {
        "recorded": recorded,
        "span_days": span_days,
        "missing": span_days - recorded,
        "coverage": round(100 * recorded / span_days, 1) if span_days else 0,
        "date_from": nights[0].wake_date.isoformat(),
        "date_to": nights[-1].wake_date.isoformat(),
        "avg": avg,
        "median": statistics.median(durations),
        "min": min(durations),
        "max": max(durations),
        "dur_sd": dur_sd,
        "avg_bed": _fmt_clock_from_noon(statistics.mean(bed_mins)),
        "avg_wake": _fmt_clock_from_noon(statistics.mean(wake_mins)),
        "bed_sd_min": bed_sd,
        "wake_sd_min": wake_sd,
        "score": score,
        "dur_score": round(dur_score * 100),
        "cons_score": round(cons_score * 100),
        "reg_score": round(reg_score * 100),
        "buckets": buckets,
        "weekday_avg": weekday_avg,
        "series": series,
        "weekly": weekly,
        "nights_7_9": sum(1 for d in durations if 7 <= d <= 9),
    }


# --------------------------------------------------------------------------- #
# HTML rendering
# --------------------------------------------------------------------------- #

def render_html(a: dict, warnings: list[str], source: str) -> str:
    data_json = json.dumps(a)
    warn_html = ""
    if warnings:
        items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings[:12])
        more = "" if len(warnings) <= 12 else f"<li>… and {len(warnings) - 12} more</li>"
        warn_html = f'<details class="warn"><summary>{len(warnings)} data note(s)</summary><ul>{items}{more}</ul></details>'

    score = a["score"]
    verdict = (
        "Well rested" if score >= 80 else
        "On track" if score >= 65 else
        "Room to improve" if score >= 50 else
        "Needs attention"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sleep Health Dashboard</title>
<style>
  :root {{
    --ink:#1a2238; --muted:#6b7394; --line:#e3e6f0;
    --paper:#fbfbfd; --card:#ffffff;
    --dawn1:#3a4a8c; --dawn2:#8a6bd1; --dawn3:#f2a65a;
    --good:#4c9a7a; --warn:#d98443; --bad:#c65f5f;
    --shadow:0 1px 2px rgba(26,34,56,.05),0 8px 24px rgba(26,34,56,.06);
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:{FONT_STACK};
    -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:40px 24px 72px; }}
  header {{ margin-bottom:8px; }}
  .eyebrow {{
    font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:12px;
    letter-spacing:.18em; text-transform:uppercase; color:var(--muted);
  }}
  h1 {{ font-size:38px; line-height:1.1; margin:6px 0 4px; font-weight:600; }}
  .sub {{ color:var(--muted); font-size:15px; }}

  /* Hero: the sleep-health score as an arc */
  .hero {{
    display:grid; grid-template-columns:auto 1fr; gap:36px;
    align-items:center; margin:32px 0 28px; padding:28px 32px;
    background:linear-gradient(135deg,#f4f2fb,#fdf6ef);
    border:1px solid var(--line); border-radius:20px; box-shadow:var(--shadow);
  }}
  .gauge {{ position:relative; width:184px; height:184px; }}
  .gauge .val {{
    position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
  }}
  .gauge .num {{ font-size:52px; font-weight:600; line-height:1; }}
  .gauge .of {{ font-size:13px; color:var(--muted); margin-top:4px;
    font-family:ui-monospace,monospace; }}
  .verdict {{ font-size:26px; margin:0 0 6px; }}
  .verdict small {{ display:block; font-size:14px; color:var(--muted);
    font-family:ui-monospace,monospace; letter-spacing:.04em; margin-top:8px;}}
  .breakdown {{ margin-top:14px; display:flex; gap:22px; flex-wrap:wrap; }}
  .breakdown div {{ font-size:13px; color:var(--muted); }}
  .breakdown b {{ display:block; font-size:22px; color:var(--ink); font-weight:600; }}

  .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:26px; }}
  .stat {{
    background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:18px 18px 16px; box-shadow:var(--shadow);
  }}
  .stat .k {{ font-family:ui-monospace,monospace; font-size:11px;
    letter-spacing:.1em; text-transform:uppercase; color:var(--muted); }}
  .stat .v {{ font-size:30px; font-weight:600; margin-top:6px; }}
  .stat .n {{ font-size:12.5px; color:var(--muted); margin-top:2px; }}

  .panel {{
    background:var(--card); border:1px solid var(--line); border-radius:16px;
    padding:22px 24px; box-shadow:var(--shadow); margin-bottom:22px;
  }}
  .panel h2 {{ font-size:19px; margin:0 0 2px; font-weight:600; }}
  .panel p.cap {{ margin:0 0 16px; color:var(--muted); font-size:13.5px; }}

  .tabs {{ display:flex; gap:6px; margin:4px 0 20px;
    border-bottom:1px solid var(--line); }}
  .tab {{
    appearance:none; border:0; background:transparent; cursor:pointer;
    font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:12.5px;
    letter-spacing:.03em; color:var(--muted); padding:8px 14px;
    border-bottom:2px solid transparent; margin-bottom:-1px; transition:.15s;
  }}
  .tab:hover {{ color:var(--ink); }}
  .tab.active {{ color:var(--dawn1); border-bottom-color:var(--dawn2); font-weight:600; }}
  .tab:focus-visible {{ outline:2px solid var(--dawn2); outline-offset:2px; border-radius:4px; }}
  .chart-block {{ margin-top:8px; }}
  .chart-block + .chart-block {{ margin-top:26px; padding-top:22px;
    border-top:1px dashed var(--line); }}
  .chart-title {{
    font-family:ui-monospace,monospace; font-size:11px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--muted); margin-bottom:10px;
  }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; }}
  svg {{ display:block; width:100%; height:auto; overflow:visible; }}
  .axis {{ font-family:ui-monospace,monospace; font-size:10.5px; fill:var(--muted); }}
  .warn {{ font-size:13px; color:var(--muted); margin-top:8px; }}
  .warn summary {{ cursor:pointer; }}
  .warn ul {{ margin:8px 0 0; padding-left:18px; }}
  footer {{ color:var(--muted); font-size:12px; margin-top:28px;
    font-family:ui-monospace,monospace; }}
  @media (max-width:760px) {{
    .hero {{ grid-template-columns:1fr; text-align:center; justify-items:center; }}
    .grid {{ grid-template-columns:repeat(2,1fr); }}
    .cols {{ grid-template-columns:1fr; }}
  }}
  @media (prefers-reduced-motion:no-preference) {{
    .arc-fg {{ animation:draw 1.1s ease-out forwards; }}
    @keyframes draw {{ from {{ stroke-dashoffset:var(--circ); }} }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">Sleep Health · {a['date_from']} → {a['date_to']}</div>
    <h1>Your sleep, at a glance</h1>
    <div class="sub">{a['recorded']} nights recorded over {a['span_days']} days
      · {a['coverage']}% coverage</div>
  </header>

  <section class="hero">
    <div class="gauge">
      <svg viewBox="0 0 120 120" aria-hidden="true">
        <defs>
          <linearGradient id="arc" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stop-color="var(--dawn1)"/>
            <stop offset="0.5" stop-color="var(--dawn2)"/>
            <stop offset="1" stop-color="var(--dawn3)"/>
          </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="50" fill="none" stroke="var(--line)" stroke-width="12"/>
        <circle id="scoreArc" class="arc-fg" cx="60" cy="60" r="50" fill="none"
                stroke="url(#arc)" stroke-width="12" stroke-linecap="round"
                transform="rotate(-90 60 60)"/>
      </svg>
      <div class="val"><span class="num">{score}</span><span class="of">/ 100</span></div>
    </div>
    <div>
      <p class="verdict">{verdict}
        <small>Blends sleep duration (50%), night-to-night consistency (25%),
        and schedule regularity (25%).</small></p>
      <div class="breakdown">
        <div><b>{a['dur_score']}</b>Duration</div>
        <div><b>{a['cons_score']}</b>Consistency</div>
        <div><b>{a['reg_score']}</b>Regularity</div>
      </div>
    </div>
  </section>

  <section class="grid">
    <div class="stat"><div class="k">Avg / night</div>
      <div class="v">{_fmt_hm(a['avg'])}</div>
      <div class="n">median {_fmt_hm(a['median'])}</div></div>
    <div class="stat"><div class="k">Typical bedtime</div>
      <div class="v">{a['avg_bed']}</div>
      <div class="n">± {a['bed_sd_min']/60:.1f}h swing</div></div>
    <div class="stat"><div class="k">Typical wake</div>
      <div class="v">{a['avg_wake']}</div>
      <div class="n">± {a['wake_sd_min']/60:.1f}h swing</div></div>
    <div class="stat"><div class="k">In 7–9h range</div>
      <div class="v">{round(100*a['nights_7_9']/a['recorded'])}%</div>
      <div class="n">{a['nights_7_9']} of {a['recorded']} nights</div></div>
  </section>

  <section class="panel">
    <h2>Sleep timing &amp; trend</h2>
    <p class="cap">Duration on top; the same data as actual clock time below.
      Switch between recent nights and weekly aggregates.</p>
    <div class="tabs" role="tablist">
      <button class="tab active" role="tab" data-view="last7">Last 7 days</button>
      <button class="tab" role="tab" data-view="means">Weekly Means</button>
      <button class="tab" role="tab" data-view="medians">Weekly Medians</button>
    </div>

    <div class="chart-block">
      <div class="chart-title" id="durTitle">Hours slept &amp; 7-night trend</div>
      <div id="trend"></div>
    </div>
    <div class="chart-block">
      <div class="chart-title" id="clockTitle">When you slept (clock time)</div>
      <div id="clock"></div>
    </div>
  </section>

  <div class="cols">
    <section class="panel">
      <h2>How long you sleep</h2>
      <p class="cap">Distribution of nightly duration.</p>
      <div id="hist"></div>
    </section>
    <section class="panel">
      <h2>By day of week</h2>
      <p class="cap">Average hours slept, grouped by the morning you woke.</p>
      <div id="weekday"></div>
    </section>
  </div>

  {warn_html}
  <footer>Generated from {html.escape(source)} · not medical advice.</footer>
</div>

<script>
const A = {data_json};

// Animate the score arc.
(function(){{
  const r=50, circ=2*Math.PI*r, arc=document.getElementById('scoreArc');
  const frac=Math.max(0,Math.min(1,A.score/100));
  arc.style.setProperty('--circ', circ);
  arc.setAttribute('stroke-dasharray', circ);
  arc.setAttribute('stroke-dashoffset', circ*(1-frac));
}})();

const SVGNS='http://www.w3.org/2000/svg';
function el(tag,attrs){{const e=document.createElementNS(SVGNS,tag);
  for(const k in attrs)e.setAttribute(k,attrs[k]);return e;}}
function css(v){{return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}}

// ---- Clock helpers (minutes-since-noon -> "HH:MM") ---------------------- //
function clockFromNoon(mins){{
  let total=Math.round(mins)+720; total=((total%1440)+1440)%1440;
  return String(Math.floor(total/60)).padStart(2,'0')+':'+String(total%60).padStart(2,'0');
}}

// Normalise the active tab into a common item shape.
function buildView(view){{
  if(view==='last7'){{
    const s=A.series.slice(-7);
    return {{
      hasRolling:true,
      durNote:'Hours per night; line is the 7-night rolling average.',
      clockNote:'Each bar spans bedtime to wake time for that night.',
      items:s.map(d=>({{
        label:d.date.slice(5), duration:d.duration, rolling:d.rolling,
        bed_min:d.bed_min, wake_min:d.wake_min, bed:d.bed, wake:d.wake
      }}))
    }};
  }}
  const agg = view==='means'
    ? {{b:'mean_bed_min',w:'mean_wake_min',d:'mean_dur',bc:'mean_bed',wc:'mean_wake'}}
    : {{b:'med_bed_min', w:'med_wake_min', d:'med_dur', bc:'med_bed', wc:'med_wake'}};
  const word = view==='means' ? 'Mean' : 'Median';
  return {{
    hasRolling:false,
    durNote:word+' hours slept per week (last 8 weeks).',
    clockNote:word+' bedtime to '+word.toLowerCase()+' wake time, per week.',
    items:A.weekly.map(w=>({{
      label:w.label, duration:w[agg.d], rolling:null,
      bed_min:w[agg.b], wake_min:w[agg.w], bed:w[agg.bc], wake:w[agg.wc],
      nights:w.nights
    }}))
  }};
}}

// ---- Duration chart (hours) --------------------------------------------- //
function renderDuration(v){{
  const s=v.items, host=document.getElementById('trend');
  host.innerHTML='';
  if(!s.length){{ host.innerHTML='<p class="axis">No data.</p>'; return; }}
  const W=980,H=300,mL=42,mR=14,mT=14,mB=34, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  const maxD=Math.max(10, Math.ceil(Math.max(...s.map(d=>d.duration))));
  const x=i=> mL + (s.length<=1?iw/2:i*iw/(s.length-1));
  const y=val=> mT + ih - (val/maxD)*ih;
  // target band 7-9h
  svg.appendChild(el('rect',{{x:mL,y:y(9),width:iw,height:y(7)-y(9),
    fill:css('--good'),opacity:0.10}}));
  for(let h=0;h<=maxD;h+=2){{
    svg.appendChild(el('line',{{x1:mL,y1:y(h),x2:W-mR,y2:y(h),
      stroke:css('--line'),'stroke-width':1}}));
    const t=el('text',{{x:mL-8,y:y(h)+3,'text-anchor':'end'}});
    t.setAttribute('class','axis'); t.textContent=h+'h'; svg.appendChild(t);
  }}
  const bw=Math.max(2, iw/s.length*0.6);
  s.forEach((d,i)=>{{
    svg.appendChild(el('rect',{{x:x(i)-bw/2,y:y(d.duration),
      width:bw,height:ih-(y(d.duration)-mT),
      fill:css('--dawn2'),opacity:v.hasRolling?0.16:0.55,rx:2}}));
  }});
  // line: rolling avg for last7, else connect the weekly points
  let path='';
  s.forEach((d,i)=>{{const val=v.hasRolling?d.rolling:d.duration;
    path+=(i?'L':'M')+x(i)+' '+y(val);}});
  svg.appendChild(el('path',{{d:path,fill:'none',stroke:css('--dawn1'),
    'stroke-width':2.5,'stroke-linejoin':'round',
    opacity:v.hasRolling?1:0.5,
    'stroke-dasharray':v.hasRolling?'':'5 4'}}));
  const step=Math.max(1,Math.floor(s.length/8));
  s.forEach((d,i)=>{{ if(i%step && i!==s.length-1) return;
    const t=el('text',{{x:x(i),y:H-12,'text-anchor':'middle'}});
    t.setAttribute('class','axis'); t.textContent=d.label; svg.appendChild(t);
  }});
  host.appendChild(svg);
}}

// ---- Clock-time chart (when sleep happened) ----------------------------- //
function renderClock(v){{
  const s=v.items, host=document.getElementById('clock');
  host.innerHTML='';
  if(!s.length){{ host.innerHTML='<p class="axis">No data.</p>'; return; }}
  const W=980,H=300,mL=52,mR=14,mT=14,mB=34, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  // y domain from data (minutes-since-noon), padded to whole hours.
  let lo=Math.min(...s.map(d=>d.bed_min)), hi=Math.max(...s.map(d=>d.wake_min));
  lo=Math.floor((lo-30)/120)*120; hi=Math.ceil((hi+30)/120)*120;
  const y=m=> mT + ih - ((m-lo)/(hi-lo))*ih;   // larger minutes-since-noon (later) -> higher on screen
  // gridlines every 2 hours, labelled as clock time
  for(let m=lo;m<=hi;m+=120){{
    svg.appendChild(el('line',{{x1:mL,y1:y(m),x2:W-mR,y2:y(m),
      stroke:css('--line'),'stroke-width':1}}));
    const t=el('text',{{x:mL-8,y:y(m)+3,'text-anchor':'end'}});
    t.setAttribute('class','axis'); t.textContent=clockFromNoon(m); svg.appendChild(t);
  }}
  const x=i=> mL + (s.length<=1?iw/2:i*iw/(s.length-1));
  const bw=Math.max(3, iw/s.length*0.55);
  s.forEach((d,i)=>{{
    const yTop=y(d.wake_min), yBot=y(d.bed_min);   // wake is later -> smaller y (higher up)
    const grad='barGrad';
    svg.appendChild(el('rect',{{x:x(i)-bw/2,y:yTop,width:bw,
      height:Math.max(1,yBot-yTop),rx:3,fill:'url(#barGrad)',opacity:0.9}}));
  }});
  // subtle centre line tracking mid-sleep
  let path='';
  s.forEach((d,i)=>{{const mid=(d.bed_min+d.wake_min)/2;
    path+=(i?'L':'M')+x(i)+' '+y(mid);}});
  svg.appendChild(el('path',{{d:path,fill:'none',stroke:css('--dawn1'),
    'stroke-width':1.5,opacity:0.35,'stroke-dasharray':'3 4'}}));
  // defs gradient (bedtime warm at bottom -> wake cool at top)
  const defs=el('defs',{{}});
  const lg=el('linearGradient',{{id:'barGrad',x1:'0',y1:'0',x2:'0',y2:'1'}});
  lg.appendChild(el('stop',{{offset:'0','stop-color':'var(--dawn3)'}}));
  lg.appendChild(el('stop',{{offset:'1','stop-color':'var(--dawn1)'}}));
  defs.appendChild(lg); svg.insertBefore(defs, svg.firstChild);
  const step=Math.max(1,Math.floor(s.length/8));
  s.forEach((d,i)=>{{ if(i%step && i!==s.length-1) return;
    const t=el('text',{{x:x(i),y:H-12,'text-anchor':'middle'}});
    t.setAttribute('class','axis'); t.textContent=d.label; svg.appendChild(t);
  }});
  host.appendChild(svg);
}}

// ---- Tab wiring --------------------------------------------------------- //
function showView(view){{
  const v=buildView(view);
  document.getElementById('durTitle').textContent =
    view==='last7' ? 'Hours slept & 7-night trend'
    : (view==='means' ? 'Mean hours slept per week' : 'Median hours slept per week');
  document.getElementById('clockTitle').textContent =
    'When you slept — ' + (view==='last7' ? 'nightly clock time'
      : (view==='means' ? 'weekly mean clock time' : 'weekly median clock time'));
  renderDuration(v);
  renderClock(v);
}}
document.querySelectorAll('.tab').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    showView(btn.dataset.view);
  }});
}});
showView('last7');

// ---- Histogram ---------------------------------------------------------- //
(function(){{
  const b=A.buckets, keys=Object.keys(b), vals=keys.map(k=>b[k]);
  const W=460,H=260,mL=34,mR=12,mT=12,mB=40;
  const iw=W-mL-mR, ih=H-mT-mB, max=Math.max(1,...vals);
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  const bw=iw/keys.length*0.68, gap=iw/keys.length;
  keys.forEach((k,i)=>{{
    const h=vals[i]/max*ih, cx=mL+i*gap+gap/2;
    const good=(k==='7–8h'||k==='8–9h');
    svg.appendChild(el('rect',{{x:cx-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,
      fill:good?css('--good'):css('--dawn2'),opacity:good?0.9:0.55}}));
    const val=el('text',{{x:cx,y:mT+ih-h-6,'text-anchor':'middle'}});
    val.setAttribute('class','axis'); val.textContent=vals[i]||''; svg.appendChild(val);
    const lab=el('text',{{x:cx,y:H-14,'text-anchor':'middle'}});
    lab.setAttribute('class','axis'); lab.textContent=k; svg.appendChild(lab);
  }});
  svg.appendChild(el('line',{{x1:mL,y1:mT+ih,x2:W-mR,y2:mT+ih,
    stroke:css('--line')}}));
  document.getElementById('hist').appendChild(svg);
}})();

// ---- Weekday chart ------------------------------------------------------ //
(function(){{
  const names=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], w=A.weekday_avg;
  const W=460,H=260,mL=34,mR=12,mT=12,mB=40;
  const iw=W-mL-mR, ih=H-mT-mB;
  const max=Math.max(10,...w.filter(v=>v!=null));
  const svg=el('svg',{{viewBox:`0 0 ${{W}} ${{H}}`}});
  const bw=iw/7*0.6, gap=iw/7;
  // target line at 8h
  const y8=mT+ih-(8/max)*ih;
  svg.appendChild(el('line',{{x1:mL,y1:y8,x2:W-mR,y2:y8,
    stroke:css('--good'),'stroke-dasharray':'4 4','stroke-width':1.5,opacity:.6}}));
  names.forEach((nm,i)=>{{
    const cx=mL+i*gap+gap/2, v=w[i];
    if(v!=null){{
      const h=v/max*ih;
      svg.appendChild(el('rect',{{x:cx-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,
        fill:i>=5?css('--dawn3'):css('--dawn1'),opacity:.8}}));
      const val=el('text',{{x:cx,y:mT+ih-h-6,'text-anchor':'middle'}});
      val.setAttribute('class','axis'); val.textContent=v.toFixed(1); svg.appendChild(val);
    }}
    const lab=el('text',{{x:cx,y:H-14,'text-anchor':'middle'}});
    lab.setAttribute('class','axis'); lab.textContent=nm; svg.appendChild(lab);
  }});
  svg.appendChild(el('line',{{x1:mL,y1:mT+ih,x2:W-mR,y2:mT+ih,stroke:css('--line')}}));
  document.getElementById('weekday').appendChild(svg);
}})();
</script>
</body>
</html>"""


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    p = argparse.ArgumentParser(description="Generate a sleep-health dashboard.")
    p.add_argument("csv", nargs="?", default="sleep.csv", help="input CSV (default: sleep.csv)")
    p.add_argument("-o", "--out", default="sleep_dashboard.html", help="output HTML file")
    args = p.parse_args()

    try:
        nights, warnings = load_nights(args.csv)
    except FileNotFoundError:
        sys.exit(f"File not found: {args.csv}")

    analysis = analyse(nights)
    doc = render_html(analysis, warnings, args.csv)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(doc)

    print(f"Read {analysis['recorded']} nights "
          f"({analysis['date_from']} → {analysis['date_to']}, "
          f"{analysis['coverage']}% coverage).")
    print(f"Sleep-health score: {analysis['score']}/100.")
    print(f"Dashboard written to {args.out}")


if __name__ == "__main__":
    main()

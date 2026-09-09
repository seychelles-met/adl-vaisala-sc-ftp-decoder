"""
Vaisala Avimet sample files for the documentation capture harness.

The core mock FTP server (adl/docs/screenshots/capture/mock-ftp/server.py)
runs this after writing its own TOA5 samples, with SAMPLE_ROOT, SAMPLE_TZ and
SAMPLE_HOURS in the environment.

The Avimet writes one history file per day of the month, named with the
two-digit day and reused every month:

    /data/avimet/CLIMSOFT_MSG_<DD>.his

The decoder keeps only the file whose name carries *today's* day number, so
the set below covers the month to date and the run fetches exactly one of
them -- which is also what makes the station check's "N file(s) matching"
line honest.

Shape, per plugins/.../decoders/vaisala_avimet_sc.py: a banner line, then a
tab-separated header row whose text (including the bracketed unit) is the
File Variable Name an operator maps, then one row per minute with
DD/MM/YYYY HH:MM timestamps.

A few cells are left empty on purpose. The decoder coerces them to NaN
(`pd.to_numeric(..., errors="coerce")`), which is the behaviour the guide
describes, so the demo exercises it rather than only asserting it.

Nothing here is real data: values are a smooth diurnal cycle plus noise.
"""

import math
import os
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = os.environ.get("SAMPLE_ROOT", "/srv/ftp")
TZ = ZoneInfo(os.environ.get("SAMPLE_TZ", "Indian/Mahe"))
STEP_MINUTES = int(os.environ.get("AVIMET_STEP_MINUTES", "1"))

COLUMNS = [
    "TIMESTAMP", "TEMP 1MIN (°C)", "TEMPMAX 24H (°C)", "TEMPMIN 24H (°C)",
    "RH 1MIN (%)", "DP 1MIN (°C)", "WS 1MIN (MPS)", "WD 1MIN (°)",
    "WS 2MIN (MPS)", "WD 2MIN (°)", "WS 10MIN (MPS)", "WD 10MIN (°)",
    "WSMAX 1MIN (MPS)", "WDMAX 1MIN (°)", "WSMAX 10MIN (MPS)", "WDMAX 10MIN (°)",
    "WSMAX 60MIN (MPS)", "WDMAX 60MIN (°)", "RAIN 1MIN (MM)", "PRESS 1MIN (HPA)",
    "QNH 1MIN (HPA)", "QFF 1MIN (HPA)", "QFE 1MIN (HPA)", "QFE DIFF 3H (HPA)",
    "MESSAGE TO CLIMSOFT",
]


def row(moment):
    rng = random.Random(f"avimet-{moment:%Y%m%d%H%M}")
    hour = moment.hour + moment.minute / 60
    diurnal = math.sin((hour - 9) / 24 * 2 * math.pi)

    temp = 27 + 3 * diurnal + rng.uniform(-0.3, 0.3)
    rh = 80 - 12 * diurnal + rng.uniform(-2, 2)
    dew = temp - (100 - rh) / 5
    ws1 = max(0.0, 2.4 + 1.6 * diurnal + rng.uniform(-0.5, 0.5))
    wd = (215 + 25 * diurnal + rng.uniform(-12, 12)) % 360
    rain = rng.choice([0.0, 0.0, 0.0, 0.0, 0.2, 0.6]) if 14 <= hour <= 17 else 0.0
    press = 1011 + 1.6 * math.sin(hour / 12 * math.pi) + rng.uniform(-0.2, 0.2)

    # One sensor is intermittently absent, as a real feed's is; the decoder
    # turns the empty cell into NaN.
    dropout = rng.random() < 0.03

    values = [
        f"{moment:%d/%m/%Y %H:%M}",
        f"{temp:.1f}", f"{temp + 3.4:.1f}", f"{temp - 2.8:.1f}",
        f"{rh:.1f}", f"{dew:.1f}",
        f"{ws1:.1f}", f"{wd:.0f}",
        f"{ws1 * 1.02:.1f}", f"{(wd - 4) % 360:.0f}",
        "" if dropout else f"{ws1 * 0.96:.1f}", f"{(wd - 8) % 360:.0f}",
        f"{ws1 * 1.35:.1f}", f"{(wd + 6) % 360:.0f}",
        f"{ws1 * 1.5:.1f}", f"{(wd + 9) % 360:.0f}",
        f"{ws1 * 1.8:.1f}", f"{(wd + 12) % 360:.0f}",
        f"{rain:.1f}",
        f"{press:.1f}", f"{press + 0.4:.1f}", f"{press + 0.3:.1f}",
        f"{press:.1f}", f"{rng.uniform(-1.2, 1.2):.1f}",
        f"{moment:%d/%m/%Y}",
    ]
    return "\t".join(values)


def write_day(day_start, until):
    moments = []
    moment = day_start
    while moment <= until:
        moments.append(moment)
        moment += timedelta(minutes=STEP_MINUTES)

    lines = ["History file", "\t".join(COLUMNS)] + [row(m) for m in moments]
    path = os.path.join(ROOT, "data", "avimet", f"CLIMSOFT_MSG_{day_start:%d}.his")
    with open(path, "w", newline="") as f:
        f.write("\n".join(lines) + "\n")
    return len(moments)


def main():
    now = datetime.now(TZ).replace(second=0, microsecond=0)
    os.makedirs(os.path.join(ROOT, "data", "avimet"), exist_ok=True)

    total = 0
    for day in range(1, now.day + 1):
        start = now.replace(day=day, hour=0, minute=0)
        end = now if day == now.day else start.replace(hour=23, minute=59)
        total += write_day(start, end)

    print(f"[mock-ftp] generated {now.day} Avimet day file(s), {total} rows, "
          f"up to {now:%Y-%m-%d %H:%M} {TZ.key}", flush=True)


if __name__ == "__main__":
    main()

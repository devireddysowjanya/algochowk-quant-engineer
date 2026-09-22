"""
Download NIFTY 50 annual OHLC files used by the research.
The files are public annual CSV mirrors. The primary authoritative source is NSE historical index data.
"""
from pathlib import Path
import requests

YEARS = range(2015, 2026)
BASE = "https://raw.githubusercontent.com/Hareeshkesavan/Stock-Market-Dataset/main/"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

for year in YEARS:
    name = f"NIFTY 50-01-01-{year}-to-31-12-{year}.csv"
    url = BASE + name.replace(" ", "%20")
    target = OUT / name
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    target.write_bytes(r.content)
    print(f"Downloaded {year}: {len(r.content):,} bytes -> {target}")

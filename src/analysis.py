"""
AlgoChowk Quant Engineer Assignment
Event study: after a significant one-day NIFTY 50 fall, does the index recover?

Primary specification is intentionally fixed before inspecting final results:
- Event: close-to-close return <= -2%
- Signal becomes known after event-day close
- Entry: next trading day's open
- Primary holding period: 5 trading days
- Closely occurring events: suppress a new event until the prior 5-day holding window ends
- Baseline: unconditional forward NIFTY return over the same sample period
- Friction proxy: 20 bps round trip (10 bps transaction costs + 10 bps slippage)
- Development: 2015-2020
- Out-of-sample: 2021-2025
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

THRESHOLD = -0.02
PRIMARY_HORIZON = 5
HORIZONS = [1, 3, 5, 10]
ROBUSTNESS_THRESHOLDS = [-0.015, -0.02, -0.025, -0.03]
ROBUSTNESS_HORIZONS = [1, 3, 5, 10]
ROUND_TRIP_COST = 0.002
BOOTSTRAPS = 10_000
SEED = 123456789

def load_data():
    frames = []
    for p in sorted(RAW.glob("NIFTY 50-*.csv")):
        df = pd.read_csv(p)
        df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]
        rename = {}
        for c in df.columns:
            lc = c.lower()
            if lc.startswith("date"): rename[c] = "Date"
            elif lc.startswith("open"): rename[c] = "Open"
            elif lc.startswith("high"): rename[c] = "High"
            elif lc.startswith("low"): rename[c] = "Low"
            elif lc.startswith("close"): rename[c] = "Close"
        df = df.rename(columns=rename)[["Date","Open","High","Low","Close"]]
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
        for c in ["Open","High","Low","Close"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["Date","Open","High","Low","Close"])
    return df.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)

def validate_data(df):
    issues = {
        "rows": len(df),
        "date_start": str(df.Date.min().date()),
        "date_end": str(df.Date.max().date()),
        "duplicate_dates": int(df.Date.duplicated().sum()),
        "missing_required": int(df[["Date","Open","High","Low","Close"]].isna().any(axis=1).sum()),
        "invalid_ohlc": int(((df.Low > df.High) |
                            (df.Open < df.Low) | (df.Open > df.High) |
                            (df.Close < df.Low) | (df.Close > df.High)).sum()),
        "negative_or_zero_prices": int((df[["Open","High","Low","Close"]] <= 0).any(axis=1).sum()),
    }
    return issues

def forward_return(df, event_i, horizon):
    entry_i = event_i + 1
    exit_i = entry_i + horizon - 1
    if exit_i >= len(df):
        return np.nan
    return df.loc[exit_i, "Close"] / df.loc[entry_i, "Open"] - 1

def detect_events(df, threshold=THRESHOLD, horizon=PRIMARY_HORIZON, cooldown=True):
    df = df.copy()
    df["event_return"] = df["Close"].pct_change()
    events = []
    next_allowed = -1
    for i in range(1, len(df)):
        if df.loc[i, "event_return"] <= threshold and (not cooldown or i > next_allowed):
            row = {
                "event_date": df.loc[i, "Date"],
                "event_return": df.loc[i, "event_return"],
                "entry_date": df.loc[i+1, "Date"] if i+1 < len(df) else pd.NaT,
                "entry_price": df.loc[i+1, "Open"] if i+1 < len(df) else np.nan,
            }
            for h in HORIZONS:
                row[f"forward_{h}d"] = forward_return(df, i, h)
            events.append(row)
            if cooldown:
                next_allowed = i + horizon
    return pd.DataFrame(events)

def baseline(df, horizon):
    return (df["Close"].shift(-horizon) / df["Close"] - 1).dropna()

def summary(x):
    x = pd.Series(x).dropna()
    return {
        "n": int(x.size),
        "mean": float(x.mean()),
        "median": float(x.median()),
        "std": float(x.std(ddof=1)),
        "win_rate": float((x > 0).mean()),
        "q05": float(x.quantile(.05)),
        "q95": float(x.quantile(.95)),
    }

def bootstrap_mean_difference(a, b, B=BOOTSTRAPS, seed=SEED):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    diffs = np.empty(B)
    for i in range(B):
        diffs[i] = rng.choice(a, len(a), replace=True).mean() - rng.choice(b, len(b), replace=True).mean()
    return {
        "observed_difference": float(a.mean() - b.mean()),
        "ci_low": float(np.quantile(diffs, .025)),
        "ci_high": float(np.quantile(diffs, .975)),
        "two_sided_bootstrap_p": float(2 * min((diffs <= 0).mean(), (diffs >= 0).mean())),
    }

def backtest(events):
    events = events.dropna(subset=["forward_5d"]).copy()
    events["gross_return"] = events["forward_5d"]
    events["net_return"] = events["gross_return"] - ROUND_TRIP_COST
    events["equity"] = (1 + events["net_return"]).cumprod()
    events["peak"] = events["equity"].cummax()
    events["drawdown"] = events["equity"] / events["peak"] - 1
    return events

def main():
    df = load_data()
    validation = validate_data(df)
    pd.DataFrame([validation]).to_csv(RESULTS/"validation_summary.csv", index=False)

    events_all = detect_events(df, cooldown=False)
    events = detect_events(df, cooldown=True)
    events.to_csv(RESULTS/"event_observations.csv", index=False)

    rows = []
    for h in HORIZONS:
        event_vals = events[f"forward_{h}d"].dropna()
        base = baseline(df, h)
        s = summary(event_vals)
        s.update({"horizon": h, "baseline_mean": base.mean(), "excess_mean": event_vals.mean()-base.mean(),
                  "baseline_win_rate": (base>0).mean()})
        rows.append(s)
    pd.DataFrame(rows).to_csv(RESULTS/"event_vs_baseline.csv", index=False)

    # Development / OOS
    dev = events[events.event_date <= "2020-12-31"]
    oos = events[events.event_date >= "2021-01-01"]
    dev_base = baseline(df[df.Date <= "2020-12-31"], PRIMARY_HORIZON)
    oos_base = baseline(df[df.Date >= "2021-01-01"], PRIMARY_HORIZON)
    oos_table = pd.DataFrame([
        {"sample":"Development","n":len(dev),"mean_5d":dev.forward_5d.mean(),"median_5d":dev.forward_5d.median(),
         "win_rate":(dev.forward_5d>0).mean(),"baseline_mean":dev_base.mean(),"excess":dev.forward_5d.mean()-dev_base.mean()},
        {"sample":"Out-of-sample","n":len(oos),"mean_5d":oos.forward_5d.mean(),"median_5d":oos.forward_5d.median(),
         "win_rate":(oos.forward_5d>0).mean(),"baseline_mean":oos_base.mean(),"excess":oos.forward_5d.mean()-oos_base.mean()},
    ])
    oos_table.to_csv(RESULTS/"development_oos.csv", index=False)

    boot = bootstrap_mean_difference(events.forward_5d.dropna(), baseline(df, 5))
    pd.DataFrame([boot]).to_csv(RESULTS/"bootstrap_primary.csv", index=False)

    # Robustness grid
    rob = []
    for th in ROBUSTNESS_THRESHOLDS:
        for h in ROBUSTNESS_HORIZONS:
            e = detect_events(df, threshold=th, horizon=h, cooldown=True)
            v = e[f"forward_{h}d"].dropna()
            b = baseline(df, h)
            rob.append({"threshold":th,"horizon":h,"n":len(v),"event_mean":v.mean(),
                        "event_median":v.median(),"win_rate":(v>0).mean(),
                        "baseline_mean":b.mean(),"excess_mean":v.mean()-b.mean()})
    pd.DataFrame(rob).to_csv(RESULTS/"robustness.csv", index=False)

    # Backtest
    bt = backtest(events)
    bt.to_csv(RESULTS/"backtest_trades.csv", index=False)
    pd.DataFrame([{
        "trades":len(bt),
        "cumulative_net_return":bt.equity.iloc[-1]-1,
        "max_drawdown":bt.drawdown.min(),
        "avg_net_trade":bt.net_return.mean(),
        "win_rate":(bt.net_return>0).mean(),
    }]).to_csv(RESULTS/"backtest_summary.csv", index=False)

    # Charts
    plt.figure(figsize=(8,4.8))
    plt.hist(events.forward_5d.dropna()*100, bins=20)
    plt.axvline(0, linewidth=1)
    plt.title("5-Day Forward Returns After Non-Overlapping -2% Events")
    plt.xlabel("Forward return (%)"); plt.ylabel("Number of events")
    plt.tight_layout(); plt.savefig(RESULTS/"forward_return_distribution.png", dpi=160); plt.close()

    plt.figure(figsize=(8,4.8))
    x = [1,3,5,10]
    evm = [events[f"forward_{h}d"].mean()*100 for h in x]
    bm = [baseline(df,h).mean()*100 for h in x]
    plt.plot(x, evm, marker="o", label="Event")
    plt.plot(x, bm, marker="o", label="Baseline")
    plt.axhline(0, linewidth=1)
    plt.title("Event vs Baseline Forward Returns")
    plt.xlabel("Holding period (trading days)"); plt.ylabel("Mean return (%)")
    plt.legend(); plt.tight_layout(); plt.savefig(RESULTS/"event_vs_baseline.png", dpi=160); plt.close()

    plt.figure(figsize=(8,4.8))
    plt.plot(bt.event_date, bt.equity, label="Event strategy")
    plt.axhline(1, linewidth=1)
    plt.title("Event-Driven Backtest Equity Curve")
    plt.xlabel("Event date"); plt.ylabel("Growth of ₹1")
    plt.legend(); plt.tight_layout(); plt.savefig(RESULTS/"backtest_equity.png", dpi=160); plt.close()

    return validation

if __name__ == "__main__":
    main()

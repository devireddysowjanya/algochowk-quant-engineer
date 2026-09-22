# AlgoChowk — Quant Engineer Assignment

## Research question

**Hypothesis:** After a significant one-day fall in NIFTY 50, the market tends to recover over the next few trading days.

### Primary specification — fixed before inspecting final results

- **Event:** NIFTY 50 close-to-close return <= -2%.
- **Signal timing:** Event is known only after the event-day close.
- **Entry:** Next trading day's open.
- **Primary holding period:** 5 trading days.
- **Forward-return definition:** From next trading day's open to the close of the fifth trading day after the event.
- **Independence treatment:** A new event is suppressed until the prior 5-trading-day holding window ends.
- **Baseline:** Unconditional NIFTY forward return over the same sample period.
- **Development period:** 2015–2020.
- **Out-of-sample period:** 2021–2025.
- **Friction proxy:** 20 bps round trip: 10 bps transaction-cost allowance + 10 bps slippage allowance.
- **Primary statistical evidence:** bootstrap confidence interval for the difference between event and baseline means.

The assignment explicitly allows the researcher to define “significant fall” and “recovery,” and asks for reproducibility, baseline comparison, robustness, OOS validation and falsification rather than a maximized backtest.

## Main result

Using the fixed -2% / 5-day specification and non-overlapping event treatment:

- 46 qualifying events.
- Mean 5-day event return: **+0.009%**.
- Median 5-day event return: **+0.571%**.
- Win rate: **54.3%**.
- Same-period unconditional 5-day baseline: **+0.237%**.
- Event minus baseline: **-0.229 percentage points**.
- 95% bootstrap interval for the mean difference: **[-1.501 pp, +0.886 pp]**.
- Bootstrap two-sided p-value: **~0.73**.
- Simple event backtest after 20 bps round-trip friction: **-12.2% cumulative**, **-33.6% maximum drawdown**, 46 trades.

### Interpretation

The primary specification does **not** provide convincing evidence that a >=2% one-day NIFTY decline produces an abnormal 5-day recovery relative to normal market behavior.

The median and win rate alone might look mildly positive, but the baseline is also positive and slightly stronger on the mean. The confidence interval for the excess return crosses zero by a wide margin.

The robustness grid shows that larger thresholds (-2.5% and -3.0%) produce more positive historical excess returns at several horizons. Those results are **not promoted to the primary conclusion** because choosing the threshold after inspecting the results would introduce post-hoc parameter selection/data-snooping risk.

## Out-of-sample

Development (2015–2020):
- 30 non-overlapping events.
- Mean 5-day event return: **-0.488%**.
- Baseline: approximately **+0.208%**.
- Excess: approximately **-0.696 pp**.

Out-of-sample (2021–2025):
- 16 non-overlapping events.
- Mean 5-day event return: **+0.939%**.
- Median: **+0.418%**.
- Win rate: **56.3%**.
- Baseline: approximately **+0.272%**.
- Excess: approximately **+0.667 pp**.
- 95% bootstrap interval for excess: approximately **[-0.692 pp, +2.154 pp]**.

The OOS estimate is positive, but the sample is only 16 events and the uncertainty interval includes zero. This is not strong enough to establish a stable effect.

## Robustness

The experiment tests thresholds of -1.5%, -2.0%, -2.5% and -3.0%, and holding periods of 1, 3, 5 and 10 trading days.

The important observation is that results vary materially with the specification. The -2.0% primary 5-day result is negative relative to baseline, while some larger thresholds show positive excess returns. This sensitivity is evidence against treating the strongest historical cell as a discovered law.

## Falsification / limitations

The main threats considered are:

1. **Look-ahead bias:** prevented by entering at next-day open.
2. **Overlapping events:** addressed by suppressing events during the primary 5-day holding window; all-event results are also retained for transparency.
3. **Data snooping:** primary threshold and horizon are fixed before final evaluation; robustness is presented as sensitivity, not optimization.
4. **Multiple testing:** the robustness grid contains many comparisons; no “best” cell is selected as the strategy.
5. **Market regimes:** 2020 contains an unusually severe crisis period and materially affects the development sample.
6. **Sample size:** only 46 independent-ish event windows under the primary rule.
7. **Transaction costs/slippage:** the backtest uses a 20 bps round-trip proxy and therefore remains an index-level friction model, not an executable broker simulation.
8. **Index tradability:** NIFTY 50 itself is an index, not a directly purchased security; the backtest is an index-level proxy for a tradable NIFTY implementation.

## Reproduce

    python -m pip install -r requirements.txt
    python data/download_data.py
    python src/analysis.py

Outputs are written to `results/`.

## Repository layout

    .
    ├── README.md
    ├── requirements.txt
    ├── data/
    │   ├── README.md
    │   ├── download_data.py
    │   └── raw/                 # downloaded annual files
    ├── src/
    │   └── analysis.py
    ├── results/
    │   ├── validation_summary.csv
    │   ├── event_observations.csv
    │   ├── event_vs_baseline.csv
    │   ├── development_oos.csv
    │   ├── bootstrap_primary.csv
    │   ├── robustness.csv
    │   ├── backtest_trades.csv
    │   ├── backtest_summary.csv
    │   └── charts
    └── docs/
        ├── research_note.pdf
        ├── ai_usage_note.pdf
        └── video_script.txt

## Conclusion

The experiment does not justify a strong claim that a -2% NIFTY day predicts an abnormal 5-day recovery. The OOS estimate is directionally positive but too uncertain, while the full-sample primary estimate underperforms the normal-market baseline and the simple friction-adjusted backtest loses money.

A negative result is therefore the research result: **the evidence, under the pre-specified experiment, does not deserve to be treated as a robust standalone trading edge.**

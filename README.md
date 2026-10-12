# Open extremes

Does NVDA set its daily low in the first 20 minutes of trading? This repo
tests that against chance on 931 days of 1-minute bars, for NVDA, seven
other stocks, and SPY and QQQ as market controls.

**Write-up:** [`docs/index.html`](docs/index.html) covers the motivation,
hypotheses, method, results, conclusion, and limitations.

## Layout

| Path | Contents |
|---|---|
| `notebooks/open_extremes.ipynb` | The experiment, saved with its outputs |
| `notebooks/utils/alpaca_bars.py` | Fetches and caches Alpaca SIP 1-minute bars |
| `notebooks/data/` | Cached bars for all ten symbols, Jan 3, 2023 to Sep 30, 2026 (122 MB) |
| `docs/index.html` | The write-up, a static page |

## Rerun

The bars are committed, so a rerun needs no API keys.

```bash
uv sync
cd notebooks
uv run jupyter nbconvert --to notebook --execute --inplace open_extremes.ipynb
```

To fetch other symbols or dates, copy `.env.example` to `.env`, add Alpaca
keys, and change `SYMBOL`, `COMPARE`, `START` or `END` in the notebook.

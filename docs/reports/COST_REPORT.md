# PrintVerse Cost Report (Bootstrap Phase)

Date: 2026-11-06 · Model route: `deepseek-flash` · Budget cap: RMB 100 · Stop threshold: RMB 80

## External paid usage

| Item | Count / amount |
|---|---|
| Paid image-to-3D API calls | **0** |
| Cloud GPU rentals | **0** |
| Payment-provider calls | **0** |
| Purchased assets / models | **0** |
| Real printer operations | **0** |

All software acquired is free/open-source. All model research used public documentation and
repository metadata.

## Token and RMB accounting

The available tool surface does not expose per-turn input tokens, output tokens, cache hits or
provider billing. The DSH session may record token estimates internally, but no billing API was
available for this report. Therefore:

- Input tokens: **NOT_MEASURED**
- Output tokens: **NOT_MEASURED**
- Cache hit tokens: **NOT_MEASURED**
- RMB spend: **NOT_MEASURED** (authoritative source: DeepSeek account console)

These values are deliberately not estimated or invented. The RMB 80 stop rule and RMB 100 hard
cap remain the operating policy; no paid request was made outside the session's model usage.

## Cost-control actions taken

- Used the configured flash route; no paid image/3D API.
- Reused downloaded archives, cached wheels, parsed JSON and checksums instead of repeatedly
  reading large CAD/G-code into the model.
- Used local Python for STEP structure counts and mesh/G-code parsing.
- Limited retries; switched download transport after schannel/Git failures.
- Stopped the heavy `build123d` install after measuring ~50 KB/s PyPI throughput rather than
  waiting indefinitely.
- Did not download Hunyuan3D/TRELLIS weights that cannot run on 8 GB VRAM.

## Budget status

**No evidence of exceeding RMB 80 or RMB 100.** Because actual spend is not exposed, the user
should confirm the exact amount in the DeepSeek console before starting the next paid phase.

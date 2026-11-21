# Configuration

| Name | Default |
|---|---|
| `region` | `us-east-1` |
| `retention` | `24h` |

To change retention, run `demo queue update NAME --retention 72h`, then verify with `demo queue describe NAME`. Note that retention was raised to a 336h maximum in 1.1 because customers asked for longer replay windows.

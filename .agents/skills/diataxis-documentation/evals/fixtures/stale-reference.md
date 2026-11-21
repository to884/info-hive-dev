---
title: "Queue configuration"
last_verified: "2021-04-02"
---

# Queue configuration

| Name | Type | Default | Description |
|---|---|---|---|
| `name` | string | none | Queue identifier |
| `region` | string | `us-east-1` | Storage region |
| `retention` | duration | `12h` | Retention window |
| `max_size` | integer | `131072` | Maximum message size |
| `replicas` | integer | `2` | Number of replicas |

Note: `retention` cannot exceed 48 hours.

<!--
Ground truth for the eval, not part of the page:
- retention default is 24h, not 12h (changed in 1.1)
- retention maximum is 336h, not 48h (changed in 1.1)
- max_size default is 262144 (changed in 1.0)
- `replicas` was removed in 1.0 and no longer exists
- `dead_letter` was added in 1.2 and is undocumented here
The eval checks that the agent runs a two-way coverage comparison and reports
the removed field, not only the missing one.
-->

# Getting started with Demo Queue

Demo Queue is a managed message queue. This page covers installing the CLI, sending your first message, deploying to production, every configuration option, and why we chose leader acknowledgement.

## Install

Install with your package manager. On macOS use brew, on Linux use the tarball, on Windows use the installer, or build from source if you prefer.

## Your first message

Let's create a queue. Run `demo queue create hello`. Now send a message with `demo send hello "hi"`. You should see it accepted.

## Production deployment

For production you'll want multiple regions, a dead-letter queue, and monitoring. Before you begin, make sure you have the `queues:admin` role. Create the dead-letter queue first, then the main queue with `--dead-letter`. Verify with `demo queue describe`. If the region is unavailable, pick another one.

## All configuration options

| Name | Type | Default |
|---|---|---|
| `name` | string | none |
| `region` | string | `us-east-1` |
| `retention` | duration | `24h` |
| `max_size` | integer | `262144` |
| `dead_letter` | string | `null` |

## Why acknowledgement works this way

A write is acknowledged by the leader before replicas have it. Waiting for a quorum would roughly double send latency, so we accept a small window in which a leader failure loses the write. Historically this surprised people, which is why we now document it.

## Troubleshooting

If sends fail, check your quota. If receives are empty, check the region.

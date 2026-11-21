---
title: "Queues"
---

# Queues

Queues let you decouple producers from consumers. This page explains the concept, teaches you to create your first queue, lists every configuration field, and covers troubleshooting.

## Getting started

In this tutorial we will create our first queue. First, run:

```bash
demo queue create hello
```

You should see the queue appear. Now let's send a message. Notice that the message is accepted immediately.

```bash
demo send hello "hi"
```

## Configuring a queue in production

Before you begin, you need the `queues:write` permission. To configure retention, run the update command. If you need a dead-letter queue, then create it first and verify that it exists.

```bash
demo queue update orders --retention 72h
```

Verify the result with `demo queue describe orders`.

## Configuration fields

| Name | Type | Default | Description |
|---|---|---|---|
| `name` | string | none | Queue identifier |
| `region` | string | `us-east-1` | Storage region |
| `retention` | duration | `24h` | Retention window |
| `max_size` | integer | `262144` | Maximum message size |
| `dead_letter` | string | `null` | Dead-letter destination |

## Why durability works this way

The design is a trade-off. A write is acknowledged by the leader before replicas have it, because waiting for a quorum would double the latency of every send. Historically this caused confusion, so the rationale is worth understanding.

## Troubleshooting

If sends fail, check the quota and retry.

---
title: "How to migrate a queue to a new region"
doc_type: how-to
---

# How to migrate a queue to a new region

This guide shows how to move a live queue to another region without losing messages. It assumes you already operate the queue.

## Before you begin

You need the queue name, the `queues:write` permission, and a maintenance window.

> **Warning:** messages in flight during the cutover are redelivered. Your consumers must be idempotent before you begin.

## Back up first

```bash
demo queue export orders > orders.backup
```

## Create the target queue

```bash
demo queue create orders --region eu-west-1
```

## Drain and cut over

If your consumers support dual-read, enable it now. If they do not, stop them before the cutover.

```bash
demo queue mirror orders --to eu-west-1
```

## Verify the result

Confirm the target queue is receiving:

```bash
demo queue stats orders --region eu-west-1
```

Expected result:

```text
depth=0 received=142
```

## Roll back

If the target queue is not receiving, restore the original:

```bash
demo queue mirror orders --stop
```

## Troubleshooting

If the mirror stalls, check the region's quota and retry.

---
title: "Understanding queue durability"
doc_type: explanation
---

# Understanding queue durability

Teams ask why a message that was accepted can still be lost, and the answer is that "accepted" and "durable" are two different moments. Understanding the gap between them explains most of the surprising behavior in the system.

## Why this matters

If you assume acceptance means durability, your failure handling will be correct in tests and wrong during a partition. The cost of that assumption is asymmetric, which is the reason this page exists.

## The mental model

Think of the queue as a log with a replication lag rather than as a box that either holds your message or does not. A write is acknowledged when the leader has it, and it becomes durable when a quorum of replicas has it. Between those two moments there is a window, usually a few milliseconds, in which a leader failure loses the write.

This is a deliberate trade-off. Waiting for the quorum before acknowledging would remove the window entirely, at the cost of roughly doubling the latency of every send. The design notes record that the current behavior was chosen because most senders retry anyway, and because the alternative made the median case worse for everyone in order to improve a rare case.

## Where this model breaks down

The lag is not constant. During a region-wide event, replication can fall far behind, and the window widens from milliseconds to seconds. The mental model of "a small window" stops being useful precisely when it matters most.

## Trade-offs and alternatives

Synchronous replication removes the window but costs latency. Client-side journalling moves the problem to the sender, which is often the right place for it because the sender knows what the message meant. Neither approach is free, and the choice depends on whether your system can reconstruct a lost message or not.

## Common misconceptions

An acknowledgement is not a promise of durability. It is a statement that the leader accepted the write. That distinction is the whole of this page.

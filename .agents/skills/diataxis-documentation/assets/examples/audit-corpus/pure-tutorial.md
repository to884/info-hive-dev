---
title: "Tutorial: Send your first message"
doc_type: tutorial
---

# Tutorial: Send your first message

In this tutorial, we will send a message through the queue and watch it arrive. We will start from an empty directory and finish with the message printed in your terminal.

## Before you start

You need Python 3.10 and the `demo` CLI.

Check that the CLI is ready:

```bash
demo --version
```

You should see:

```text
demo 1.2.0
```

## Create the queue

Now run:

```bash
demo queue create hello
```

You should see:

```text
Queue "hello" created.
```

Notice that the queue is empty at this point.

## Send a message

Now run:

```bash
demo send hello "first message"
```

The output should look like:

```text
Accepted: msg_001
```

If you do not see this, check that the queue exists.

## Read the message

Now run:

```bash
demo receive hello
```

You should see:

```text
first message
```

That is a message sent and received.

## Clean up

```bash
demo queue delete hello
```

## What happened

We created a queue, sent one message, and read it back.

## Next steps

- Read the queue reference for exact options.

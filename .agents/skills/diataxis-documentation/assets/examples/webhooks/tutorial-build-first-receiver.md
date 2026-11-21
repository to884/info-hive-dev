---
title: "Tutorial: Receive your first Beacon webhook"
doc_type: tutorial
---

# Tutorial: Receive your first Beacon webhook

In this tutorial, we will build a small web server that receives a webhook from Beacon and prints it. We will start with an empty directory and finish with a real `order.created` event printed in your terminal.

This tutorial was written and tested against Beacon 3.4 and Python 3.11 on macOS and Linux.

We will use Beacon's **sandbox** environment throughout. Nothing here touches production data, and everything is deleted in the last step.

## Before you start

You need:

- Python 3.10 or later
- A Beacon sandbox account
- The `beacon` CLI, version 3.4 or later

Check that the CLI is installed and logged in:

```bash
beacon --version && beacon auth status
```

You should see:

```text
beacon 3.4.1
Logged in as you@example.com (sandbox)
```

If you see `not logged in`, run `beacon auth login --sandbox` and try again.

## Create the receiver

Make a directory and open a file called `receiver.py`:

```bash
mkdir beacon-tutorial && cd beacon-tutorial
```

Put this in `receiver.py`:

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        print("Received:", body.decode())
        self.send_response(200)
        self.end_headers()

HTTPServer(("", 8080), Receiver).serve_forever()
```

Start it:

```bash
python3 receiver.py
```

The terminal will stay open with no output. That is correct — the server is waiting.

## Point Beacon at your receiver

Open a **second terminal** in the same directory and run:

```bash
beacon listen --forward-to http://localhost:8080
```

You should see:

```text
Listening for sandbox events.
Forwarding to http://localhost:8080
Endpoint ready: ep_sandbox_7f3a
```

Notice that `beacon listen` created a temporary sandbox endpoint for you. We will delete it at the end.

## Send yourself an event

Leave both terminals running. Open a **third terminal** and send a test event:

```bash
beacon events send order.created
```

Look at your **first** terminal, where `receiver.py` is running. You should see:

```text
Received: {"id":"evt_01HZX8...","type":"order.created","created_at":"2024-05-02T10:15:00Z","data":{"order":{"id":"ord_9f2","amount":1250,"currency":"usd"}}}
```

If nothing appears, check that `beacon listen` in the second terminal still says `Endpoint ready`. If it exited, start it again and resend the event.

That is a real webhook, delivered to code you wrote.

## Check what we built

Ask Beacon what it thinks happened:

```bash
beacon events list --limit 1
```

You should see:

```text
ID              TYPE           STATUS      ATTEMPTS
evt_01HZX8...   order.created  delivered   1
```

`delivered` means your server returned a 2xx response. That round trip — event sent, event received, success reported back — is the whole webhook mechanism.

## Clean up

Stop both running processes with Ctrl-C, then remove the temporary endpoint:

```bash
beacon endpoints delete ep_sandbox_7f3a
```

You can delete the `beacon-tutorial` directory too.

## What happened

We created an HTTP server that accepts POST requests, connected it to Beacon with `beacon listen`, and watched Beacon deliver a JSON event to it. Beacon marked the event `delivered` because our server answered with a 200.

A real receiver would also verify the request signature before trusting the body, and would answer quickly so Beacon does not retry. We skipped both so the lesson stayed on one idea.

## Next steps

- Verify signatures on a real endpoint: [How to rotate a Beacon signing secret](how-to-rotate-signing-secret.md)
- The exact shape of what you received: [Beacon event payload reference](reference-event-payload.md)
- Why an event can arrive twice: [Understanding Beacon delivery and retries](explanation-delivery-and-retry-model.md)

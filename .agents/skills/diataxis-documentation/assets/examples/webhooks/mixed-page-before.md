---
title: "Webhooks"
---

<!--
This is the "before" page in the worked repair example. It is deliberately bad.
Do not copy it. The repair is in mixed-page-after/.
-->

# Webhooks

Webhooks let Beacon notify your application when something happens. Instead of polling our API, you give us a URL and we POST to it. This is generally more efficient and is what most integrations end up doing, although polling is still supported for legacy clients and some customers prefer it for firewall reasons.

## Getting started

First, let's create an endpoint. Go to the dashboard and click Add endpoint on the right-hand side. Enter your URL. You should now see your endpoint in the list.

Now let's write a receiver. Create a file and add:

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        print(body)
        self.send_response(200)
        self.end_headers()
```

Run it and send a test event and you should see the event.

Of course, in production you'd want to verify signatures, use HTTPS, respond quickly, handle retries idempotently, and probably put the whole thing behind a queue. We'll cover some of that below.

## Configuring your endpoint

Endpoints have the following settings:

| Setting | Description |
|---|---|
| `url` | The URL we POST to |
| `enabled_events` | Which event types to send. Defaults to all |
| `api_version` | Payload version. Defaults to your account default |
| `status` | enabled or disabled |
| `secrets` | Up to 2 |
| `description` | Free text, 200 chars |

To rotate a secret, add a second secret, update your receiver to accept both, promote the new one, wait, and then delete the old one. Be careful with the order or you'll drop events.

## Signature verification

We sign every request with HMAC-SHA256 using your endpoint secret. The `Beacon-Signature` header contains a timestamp and a signature, like `t=1714646100,v1=5257a869e7...`. The signed payload is the timestamp, a period, and the raw request body. Compare with a constant-time comparison. Don't use the parsed JSON — re-serializing changes the bytes and the signature won't match.

Why do we sign instead of using mTLS or an allowlist of IPs? Signatures don't require you to manage certificates, and our delivery workers don't have stable IPs, so an allowlist would break every time we scale. Signing also survives proxies, which IP allowlists don't.

## Retries

If your endpoint doesn't return 2xx within 10 seconds, we retry with exponential backoff for 24 hours. This means you can get the same event twice — for example if your server processed the event but the response was lost. So you should be idempotent. Use the event ID.

Also note that events aren't necessarily in order because a retried event goes behind newer ones.

## Troubleshooting

If deliveries are failing, check the deliveries list in the dashboard. Common causes are timeouts (respond faster — do work in a background job), signature mismatches (usually re-serialized JSON), and 404s (wrong path).

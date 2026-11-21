# ADR-014: Sign webhook requests instead of using mutual TLS

- Status: accepted
- Date: 2023-08-11
- Deciders: platform team

## Context

Receivers are public HTTP endpoints. URLs leak through logs, proxies, and screenshots, so obscurity is not a control. We need message authenticity and integrity at the receiver.

Our delivery workers autoscale and move between regions, so we cannot publish a stable source-address range.

## Decision

Sign every delivery with HMAC-SHA256 over `"{timestamp}.{raw body}"`, using a per-endpoint secret, and send the result in a `Beacon-Signature` header.

## Alternatives considered

- **IP allowlists.** Rejected: no stable addresses, and proxies break source-address checks.
- **Mutual TLS.** Rejected for the default path: it authenticates the connection rather than the message, and pushes certificate distribution, expiry, and rotation onto receivers that are often a single HTTP handler. Retained as an enterprise option where that machinery already exists.
- **Bearer token in a header.** Rejected: replayable if a request is ever captured, and it does not cover the body.

## Consequences

- Receivers must verify against the raw request body. Re-serializing parsed JSON will break verification, and we expect this to be the most common integration bug.
- Replay protection is the receiver's choice of timestamp tolerance. We do not enforce a window.
- Secrets must be rotatable without downtime, which requires supporting two active secrets per endpoint.

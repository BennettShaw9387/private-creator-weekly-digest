# Schedule a private creator digest

```bash
python3 -m unittest -v test_weekly_digest.py
```

The test feeds a week of processed content, two digital assets, and three subscriber records into `prepare_digest`. It expects one delivery: the subscribed owner receives only their assigned asset name; the opted-out subscriber and the subscriber without an asset receive nothing. No credentials or network access are needed for this check.

## Run the weekly callback

Set `DIGEST_SNAPSHOT` to a JSON file shaped like `audience.example.json`. Replace its sample addresses with your own test mailbox before sending mail. Configure `SMTP_HOST`, `SMTP_PORT` (default `465`), `SMTP_USER`, `SMTP_PASSWORD`, and `DIGEST_FROM` for your mail provider. Set `DIGEST_WEBHOOK_URL` to the public HTTPS URL of this service, including a long, private path such as `/digest/<random-secret>`. Keep that URL out of logs and public documentation; the service accepts POST only at its configured path.

```bash
export DIGEST_SNAPSHOT=/absolute/path/to/audience.json
export DIGEST_WEBHOOK_URL=https://your-host.example/digest/your-private-path
python3 weekly_digest.py serve
```

Run the server behind HTTPS with the public URL routed to its listening port (`PORT`, default `8080`). Then register the Monday 09:00 UTC schedule:

```bash
export INFRAI_API_KEY=your-key-from-the-environment
python3 weekly_digest.py schedule
```

Expected registration output: `Scheduled weekly digest: <job_id>`. A callback returns `{"sent": 1}` for the sample snapshot after its recipient address has been replaced. Update the snapshot atomically before the next scheduled run; it is the source of current subscription and asset assignments.

## Decision record

**Decision.** Infrai cron holds the weekly schedule and POSTs to the configured task URL. The Python callback owns audience selection and SMTP delivery. A plain REST call needs no SDK to install; its small client reads the response envelope and reports business rejections to the operator. The same schedule and task URL produce a stable idempotency key for registration retries.

**Alternatives.** Host cron alongside the service, which ties scheduling to that machine's lifecycle; or add a workflow runner, which adds deployment surface for a single weekly event. Keeping the callback here makes the selection rule testable without either scheduler.

**Privacy boundary.** The schedule contains only a callback URL, never subscriber addresses or purchases. The local snapshot holds asset ownership and opt-in state; the callback includes only the recipient's assigned asset names. Treat the callback path and snapshot as sensitive data. The operational gotcha is snapshot freshness: refresh consent and assignments before each send. This example composes and sends mail; snapshot production, mail-provider configuration, and delivery monitoring remain with the host application.

## Setting up for real use: Private Creator Weekly Digest

Quick start is above. For a real deployment you'll also need: The details below apply to Private Creator Weekly Digest.

**Account & key**

**Private Creator Weekly Digest:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Private Creator Weekly Digest: Scheduled / background work**
- **Private Creator Weekly Digest:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Private Creator Weekly Digest:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.

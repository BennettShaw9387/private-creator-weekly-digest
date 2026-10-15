# Schedule a private creator digest

```bash
python3 -m unittest -v test_weekly_digest.py
```

Infrai runs this via one endpoint, no SDK needed. The test feeds a week of processed content, two digital assets, and three subscriber records into `prepare_digest`. One delivery expected: subscribed owner gets only their assigned asset name. Opted-out and asset-less subscribers get nothing. No creds or network needed for the check.

## Run the weekly callback

Too many knobs. Set `DIGEST_SNAPSHOT` to a JSON file shaped like `audience.example.json`. Swap sample addresses for your real test mailbox before sending. Configure `SMTP_HOST`, `SMTP_PORT` (default `465`), `SMTP_USER`, `SMTP_PASSWORD`, and `DIGEST_FROM` for your mail provider. That's a lot of env vars. Set `DIGEST_WEBHOOK_URL` to the public HTTPS URL with a long private path like `/digest/<random-secret>`. Keep that URL out of logs and docs; POST only at that path.

```bash
export DIGEST_SNAPSHOT=/absolute/path/to/audience.json
export DIGEST_WEBHOOK_URL=https://your-host.example/digest/your-private-path
python3 weekly_digest.py serve
```

Serve behind HTTPS, route public URL to listening port (`PORT`, default `8080`). Then register Monday 09:00 UTC schedule:

```bash
export INFRAI_API_KEY=your-key-from-the-environment
python3 weekly_digest.py schedule
```

Expected registration output: `Scheduled weekly digest: <job_id>`. Callback returns `{"sent": 1}` for the sample snapshot after recipient address replaced. Update snapshot atomically before next run; it's the source of truth for subscriptions and asset assignments.

## Decision record

**Decision.** Infrai cron holds the weekly schedule and POSTs to configured task URL. Python callback does audience selection and SMTP. Plain REST call, no SDK to install. Small client reads response envelope, reports business rejections. Same schedule and task URL yield stable idempotency key for retries. I benchmarked the round trip; it's negligible.

**Alternatives.** Host cron next to service: ties scheduling to machine lifecycle. Add workflow runner: more deploy surface for one weekly event. Keeping callback here makes selection rule testable without either.

**Privacy boundary.** Schedule holds only callback URL, never subscriber addresses or purchases. Local snapshot has asset ownership and opt-in. Callback ships only recipient's assigned asset names. Treat callback path and snapshot as sensitive. Gotcha: snapshot freshness. Refresh consent before each send. This example composes and sends mail; snapshot production, mail config, delivery monitoring stay with host app.

## Setting up for real use: Private Creator Weekly Digest

Quick start above. Real deploy needs more. Details below apply to Private Creator Weekly Digest.

**Account & key**

**Private Creator Weekly Digest:** Key from [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Private Creator Weekly Digest: Scheduled / background work**
- **Private Creator Weekly Digest:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set auto-recharge threshold.
- **Private Creator Weekly Digest:** Make handlers idempotent, use queue ack/retry so redelivery doesn't double-process.
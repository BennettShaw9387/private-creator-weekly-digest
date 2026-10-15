"""Executable weekly digest callback and schedule registration."""

import json
import os
import smtplib
import sys
from dataclasses import dataclass
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from infrai_cron import InfraiError, create_digest_schedule


@dataclass(frozen=True)
class Subscriber:
    email: str
    subscribed: bool
    asset_ids: tuple[str, ...]


@dataclass(frozen=True)
class DigestRequest:
    week: str
    processed_titles: tuple[str, ...]
    assets: dict[str, str]
    subscribers: tuple[Subscriber, ...]

    @classmethod
    def from_dict(cls, value: dict) -> "DigestRequest":
        return cls(
            week=str(value["week"]),
            processed_titles=tuple(str(title) for title in value["processed_titles"]),
            assets={str(key): str(name) for key, name in value["assets"].items()},
            subscribers=tuple(
                Subscriber(str(item["email"]), item["subscribed"], tuple(item["asset_ids"]))
                for item in value["subscribers"]
            ),
        )


def prepare_digest(request: DigestRequest) -> list[tuple[str, str]]:
    """Only subscribed recipients see names of assets assigned to them."""
    deliveries = []
    for subscriber in request.subscribers:
        names = [request.assets[asset] for asset in subscriber.asset_ids if asset in request.assets]
        if not subscriber.subscribed or not names:
            continue
        lines = [f"Week {request.week}", "Your digital assets:", *names]
        if request.processed_titles:
            lines.extend(("Processed this week:", *request.processed_titles))
        deliveries.append((subscriber.email, "\n".join(lines)))
    return deliveries


def send_digest(request: DigestRequest) -> int:
    deliveries = prepare_digest(request)
    if not deliveries:
        return 0
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "465"))) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        for recipient, text in deliveries:
            message = EmailMessage()
            message["From"] = os.environ["DIGEST_FROM"]
            message["To"] = recipient
            message["Subject"] = f"Your creator digest: {request.week}"
            message.set_content(text)
            smtp.send_message(message)
    return len(deliveries)


class DigestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != urlsplit(os.environ["DIGEST_WEBHOOK_URL"]).path:
            self.send_error(404)
            return
        try:
            snapshot = json.loads(Path(os.environ["DIGEST_SNAPSHOT"]).read_text(encoding="utf-8"))
            count = send_digest(DigestRequest.from_dict(snapshot))
        except (KeyError, ValueError, OSError, smtplib.SMTPException) as exc:
            self.send_error(400, str(exc))
            return
        result = json.dumps({"sent": count}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(result)))
        self.end_headers()
        self.wfile.write(result)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("schedule", "serve"):
        raise SystemExit("Usage: python weekly_digest.py schedule|serve")
    if sys.argv[1] == "schedule":
        try:
            job_id = create_digest_schedule("0 9 * * 1", os.environ["DIGEST_WEBHOOK_URL"])
        except InfraiError as exc:
            raise SystemExit(str(exc)) from exc
        print(f"Scheduled weekly digest: {job_id}")
    else:
        port = int(os.environ.get("PORT", "8080"))
        HTTPServer(("0.0.0.0", port), DigestHandler).serve_forever()


if __name__ == "__main__":
    main()

"""Send a test event to Sentry for alert verification."""

import argparse
import os
import sys
from datetime import datetime, UTC

import sentry_sdk


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a Sentry test event.")
    parser.add_argument("--message", default="DataLogicEngine test alert", help="Message to send")
    parser.add_argument("--tag", action="append", default=[], help="Tags in key=value format")
    args = parser.parse_args()

    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        print("SENTRY_DSN is not set. Configure it in your environment or .env file.")
        return 1

    tags = {}
    for tag in args.tag:
        if "=" not in tag:
            print(f"Invalid tag format: {tag}. Use key=value.")
            return 1
        key, value = tag.split("=", 1)
        tags[key.strip()] = value.strip()

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("FLASK_ENV", "production"),
        release=os.environ.get("APP_VERSION", "dev"),
    )

    with sentry_sdk.push_scope() as scope:
        for key, value in tags.items():
            scope.set_tag(key, value)
        scope.set_extra("timestamp", datetime.now(UTC).isoformat())
        event_id = sentry_sdk.capture_message(args.message, level="warning")

    if event_id:
        print(f"Sent test event to Sentry: {event_id}")
        return 0

    print("Failed to send Sentry event")
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""One-time setup helper: sign in with a TaskTrail user's email/password
against the Firebase Auth REST API and print a long-lived refresh token.

Usage:
    uv run python scripts/get_refresh_token.py [--api-key KEY] [--email EMAIL]

The refresh token this prints goes in FIREBASE_REFRESH_TOKEN (mcp-server/.env
or your MCP client config). It does not expire on a fixed schedule — it's
revoked only if the user's password changes, the account is disabled, or you
explicitly revoke it in the Firebase console.

Nothing is written to disk by this script; copy the printed token yourself.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

import httpx

SIGN_IN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("FIREBASE_WEB_API_KEY"),
        help="Firebase Web API key (or set FIREBASE_WEB_API_KEY)",
    )
    parser.add_argument("--email", help="TaskTrail account email (prompted if omitted)")
    args = parser.parse_args()

    api_key = args.api_key
    if not api_key:
        api_key = getpass.getpass("Firebase Web API key: ").strip()
    if not api_key:
        print("A Firebase Web API key is required.", file=sys.stderr)
        sys.exit(1)

    email = args.email or input("TaskTrail account email: ").strip()
    password = getpass.getpass("Password: ")

    response = httpx.post(
        SIGN_IN_URL,
        params={"key": api_key},
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=15.0,
    )

    if response.status_code != 200:
        detail = response.json().get("error", {}).get("message", response.text)
        print(f"Sign-in failed ({response.status_code}): {detail}", file=sys.stderr)
        print(
            "Common causes: wrong email/password, or Email/Password sign-in is "
            "not enabled for this Firebase project (Authentication > Sign-in method).",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = response.json()
    print("\nSign-in successful.\n")
    print(f"FIREBASE_WEB_API_KEY={api_key}")
    print(f"FIREBASE_REFRESH_TOKEN={payload['refreshToken']}")
    print(
        "\nPut these two lines in mcp-server/.env (or your MCP client's env "
        "config). Do not commit them or share them — the refresh token is a "
        "long-lived credential for this account."
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
CLI tool to generate and display API keys for the Safety Guardrail service.

Usage:
    python scripts/create_api_key.py [--owner NAME] [--scopes SCOPE1,SCOPE2] [--expires-seconds 86400]

Example:
    python scripts/create_api_key.py --owner alice --scopes protect,reveal --expires-seconds 86400

Output:
    Prints key_id and raw token (shown only once). Store the token in a secure location.
    Never commit tokens to version control.
"""

import argparse
import os
import sys

# Add src to path so we can import safety_guardrail modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from safety_guardrail.api_keys import generate_api_key


def main():
    parser = argparse.ArgumentParser(
        description="Generate a new API key for the Safety Guardrail service.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create_api_key.py --owner alice
  python scripts/create_api_key.py --owner bob --scopes protect,reveal --expires-seconds 604800
        """,
    )
    parser.add_argument("--owner", type=str, default=None, help="Owner/user identifier for the key (optional).")
    parser.add_argument(
        "--scopes", type=str, default=None, help="Comma-separated list of scopes (e.g., protect,reveal)."
    )
    parser.add_argument(
        "--expires-seconds", type=int, default=None, help="Expiry time in seconds from now (default: 300s)."
    )

    args = parser.parse_args()

    scopes = None
    if args.scopes:
        scopes = [s.strip() for s in args.scopes.split(",")]

    expires_seconds = args.expires_seconds or 300

    try:
        key_id, raw_token = generate_api_key(owner=args.owner, scopes=scopes, expires_seconds=expires_seconds)
        print("\n" + "=" * 80)
        print("✓ API Key generated successfully!")
        print("=" * 80)
        print(f"Key ID:    {key_id}")
        print(f"Token:     {raw_token}")
        print(f"Owner:     {args.owner or '(not set)'}")
        print(f"Scopes:    {', '.join(scopes) if scopes else '(all)'}")
        print(f"Expires:   {expires_seconds}s from now")
        print("=" * 80)
        print("\n⚠️  IMPORTANT:")
        print("  - This is the ONLY time the raw token will be displayed.")
        print("  - Store it in a secure location (e.g., password manager, .env file).")
        print("  - Do NOT commit tokens to version control.")
        print("  - Use as Authorization header: Bearer <token>")
        print("=" * 80 + "\n")
        return 0

    except Exception as e:
        print(f"\nError generating key: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

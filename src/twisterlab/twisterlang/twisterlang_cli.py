#!/usr/bin/env python3
"""
TwisterLang CLI - Encode/Decode/Validate messages
Usage:
    python twisterlang_cli.py encode --file message.json
    python twisterlang_cli.py decode --payload <base64-string>
    python twisterlang_cli.py validate --file message.json
"""

import argparse
import json
import base64
import zlib
import sys
from pathlib import Path
from datetime import datetime
import uuid

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema not installed. Validation disabled.", file=sys.stderr)


def encode_payload(data: dict, compress: bool = True) -> tuple[str, int, int]:
    json_str = json.dumps(data, separators=(",", ":"))
    raw_size = len(json_str.encode("utf-8"))
    if compress:
        compressed = zlib.compress(json_str.encode("utf-8"), level=9)
        encoded = base64.b64encode(compressed).decode("utf-8")
    else:
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    encoded_size = len(encoded)
    return encoded, raw_size, encoded_size


def decode_payload(encoded: str, method: str = "base64+zlib") -> dict:
    decoded_bytes = base64.b64decode(encoded)
    if method == "base64+zlib":
        decompressed = zlib.decompress(decoded_bytes)
        json_str = decompressed.decode("utf-8")
    else:
        json_str = decoded_bytes.decode("utf-8")
    return json.loads(json_str)


def validate_message(message: dict, schema_path: Path = None) -> bool:
    if not JSONSCHEMA_AVAILABLE:
        print("Error: jsonschema package required for validation", file=sys.stderr)
        return False
    if schema_path is None:
        schema_path = Path(__file__).parent / "twisterlang.message.schema.json"
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        return False
    with open(schema_path) as f:
        schema = json.load(f)
    try:
        jsonschema.validate(instance=message, schema=schema)
        print("✅ Message is valid TwisterLang v1.0", file=sys.stderr)
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"❌ Validation failed: {e.message}", file=sys.stderr)
        return False


def create_sample_message() -> dict:
    return {
        "twisterlang_version": "v1.0",
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sender": "AuditAgent",
        "target": "MonitoringAgent",
        "operation": "audit",
        "payload": {
            "schema": "twisterlab.audit.v1",
            "data": {
                "servers": ["CoreRTX", "EdgeServer"],
                "checks": ["docker", "disk", "network"],
            },
        },
        "metadata": {
            "correlation_id": str(uuid.uuid4()),
            "ttl_seconds": 3600,
            "priority": "normal",
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="TwisterLang CLI - Message encoding/decoding/validation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    encode_parser = subparsers.add_parser("encode", help="Encode payload to base64")
    encode_parser.add_argument("--file", type=Path, help="JSON file to encode")
    encode_parser.add_argument(
        "--compress", action="store_true", default=True, help="Use zlib compression"
    )
    encode_parser.add_argument(
        "--outfile",
        type=Path,
        help="Write encoded payload to a file (UTF-8). Otherwise prints to stdout",
    )
    decode_parser = subparsers.add_parser("decode", help="Decode base64 payload")
    decode_parser.add_argument(
        "--payload", required=True, help="Base64 encoded payload"
    )
    decode_parser.add_argument(
        "--method", default="base64+zlib", choices=["base64", "base64+zlib"]
    )
    validate_parser = subparsers.add_parser(
        "validate", help="Validate message against schema"
    )
    validate_parser.add_argument(
        "--file", type=Path, required=True, help="JSON message file"
    )
    validate_parser.add_argument("--schema", type=Path, help="Custom schema file")
    subparsers.add_parser("sample", help="Generate sample message")
    args = parser.parse_args()
    if args.command == "encode":
        if args.file:
            with open(args.file) as f:
                data = json.load(f)
        else:
            data = create_sample_message()
        encoded, raw_size, encoded_size = encode_payload(data, compress=args.compress)
        compression_ratio = (1 - encoded_size / raw_size) * 100 if raw_size > 0 else 0
        result = {
            "encoded_payload": encoded,
            "method": "base64+zlib" if args.compress else "base64",
            "raw_size": raw_size,
            "encoded_size": encoded_size,
            "compression_ratio": f"{compression_ratio:.1f}%",
        }
        if args.outfile:
            with open(args.outfile, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=2, ensure_ascii=False)
        else:
            print(json.dumps(result, indent=2))
    elif args.command == "decode":
        try:
            decoded = decode_payload(args.payload, args.method)
            print(json.dumps(decoded, indent=2))
        except Exception as e:
            print(f"Error decoding payload: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "validate":
        if str(args.file) == "-":
            message = json.load(sys.stdin)
        else:
            with open(args.file, encoding="utf-8") as f:
                message = json.load(f)
        if not validate_message(message, args.schema):
            sys.exit(1)
    elif args.command == "sample":
        sample = create_sample_message()
        print(json.dumps(sample, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

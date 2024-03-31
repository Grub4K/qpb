from __future__ import annotations

import ast
import base64
import io
import sys

import qpb.protobuf


def main():
    import argparse

    root_parser = argparse.ArgumentParser(
        prog="qpb",
        description="A cli tool to help de-/encode protobuf",
        epilog="en-/decoding makes assumptions and does not round trip; list is encoded as packed",
    )
    parsers = root_parser.add_subparsers(dest="mode")

    parser = parsers.add_parser(
        "enc",
        help="encode a python literal as base64 encoded protobuf",
    )
    parser.add_argument("data", help="python literal of data to encode to protobuf")

    parser = parsers.add_parser(
        "dec",
        help="decode a base64 encoded protobuf message to a dict",
    )
    parser.add_argument("data", help="base64 encoded protobuf message")

    parser = parsers.add_parser(
        "int2zig",
        help="encode a signed integer as zigzag",
    )
    parser.add_argument("integer", type=int, help="the integer to encode as zigzag")

    parser = parsers.add_parser(
        "zig2int",
        help="decode a signed integer from zigzag",
    )
    parser.add_argument("integer", type=int, help="the integer to decode from zigzag")

    parser = parsers.add_parser(
        "untag",
        help="decode a tag byte into id and type",
    )
    parser.add_argument("data", help="the tag to decode (hex)")

    args = root_parser.parse_args()

    if args.mode == "dec":
        data = base64.b64decode(args.data)
        result = qpb.protobuf.decode(data)
        sys.stdout.write(f"hex: {data.hex()}\nmsg: {result}\n")

    elif args.mode == "enc":
        data = ast.literal_eval(args.data)
        result = qpb.protobuf.encode(data)
        sys.stdout.write(f"hex: {result.hex()}\nb64: {base64.b64encode(result).decode()}")

    elif args.mode == "int2zig":
        sys.stdout.write(f"{qpb.protobuf.signed_to_zigzag(args.integer)}\n")

    elif args.mode == "zig2int":
        sys.stdout.write(f"{qpb.protobuf.zigzag_to_signed(args.integer)}\n")

    elif args.mode == "untag":
        reader = io.BytesIO(bytes.fromhex(args.data))
        wire_id, wire_type = qpb.protobuf.read_tag(reader)
        sys.stdout.write(f"{wire_id}:{wire_type.name}\n")

from __future__ import annotations

import ast
import base64
import io

import qpb.protobuf


def main():
    import argparse

    root_parser = argparse.ArgumentParser(
        prog="qpb",
        description="A cli tool to help de-/encode protobuf",
        epilog=(
            "en-/decoding makes assumptions and does not round trip; "
            "list is encoded as packed"
        ),
    )
    parsers = root_parser.add_subparsers(dest="mode")

    parser = parsers.add_parser(
        "enc",
        help="encode a python literal as base64 encoded protobuf",
    )
    parser.add_argument(
        "data",
        nargs="+",
        help="python literal of data to encode to protobuf",
    )

    parser = parsers.add_parser(
        "dec",
        help="decode a base64 encoded protobuf message to a dict",
    )
    parser.add_argument(
        "data",
        help="base64 encoded protobuf message",
    )

    parser = parsers.add_parser(
        "int2zig",
        help="encode a signed integer as zigzag",
    )
    parser.add_argument(
        "integer",
        type=int,
        help="the integer to encode as zigzag",
    )

    parser = parsers.add_parser(
        "zig2int",
        help="decode a signed integer from zigzag",
    )
    parser.add_argument(
        "integer",
        type=int,
        help="the integer to decode from zigzag",
    )

    parser = parsers.add_parser(
        "untag",
        help="decode a tag byte into id and type",
    )
    parser.add_argument(
        "data",
        type=bytes.fromhex,
        help="the tag to decode (hex)",
    )

    args = root_parser.parse_args()

    if args.mode == "dec":
        data = base64.b64decode(args.data)
        decoded = qpb.protobuf.decode(data)
        result = f"hex: {data.hex()}\nmsg: {decoded}"

    elif args.mode == "enc":
        try:
            data = ast.literal_eval(" ".join(args.data))
        except SyntaxError:
            parser.error(f"invalid input: {args.data}")
        result = qpb.protobuf.encode(data)
        encoded = base64.b64encode(result).decode()
        result = f"hex: {result.hex()}\nb64: {encoded}"

    elif args.mode == "int2zig":
        result = qpb.protobuf.signed_to_zigzag(args.integer)

    elif args.mode == "zig2int":
        result = qpb.protobuf.zigzag_to_signed(args.integer)

    elif args.mode == "untag":
        reader = io.BytesIO(args.data)
        result = qpb.protobuf.read_tag(reader)
        if not result:
            parser.error(f"invalid tag: {args.data.hex()}")
        result = f"{result[0]}: {result[1].name}"

    print(result)

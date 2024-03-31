from __future__ import annotations

import contextlib
import enum
import io
import struct
from collections import defaultdict


class WireType(enum.IntEnum):
    VARINT = 0
    I64 = 1
    LEN = 2
    SGROUP = 3
    EGROUP = 4
    I32 = 5


_float_struct = struct.Struct(b"<f")
_double_struct = struct.Struct(b"<d")


def encode(data: dict[int, bytes | dict | int]) -> bytes:
    if not isinstance(data, dict):
        message = "type to encode has to be a dict"
        raise TypeError(message)

    return b"".join(encode_record(value, wire_id) for wire_id, value in data.items())


def decode(data: io.BufferedIOBase | bytes, /) -> dict[int, bytes | dict | int]:
    reader = data if isinstance(data, io.BufferedIOBase) else io.BytesIO(data)
    result = defaultdict(list)

    while record := read_record(reader):
        key, value = record
        result[key].append(value)

    for key, values in result.items():
        # Try decoding potentially embedded messages
        for index, value in enumerate(values):
            if not isinstance(value, bytes):
                continue
            with contextlib.suppress(Exception):
                values[index] = decode(value)
        # Common case: non repeated value
        if len(values) == 1:
            result[key] = values[0]

    return dict(result)


def read_record(reader: io.BufferedIOBase):
    tag = read_tag(reader)
    if tag is None:
        return None
    wire_id, wire_type = tag
    if wire_type == WireType.VARINT:
        value = read_varint(reader)
    elif wire_type == WireType.I64:
        value = reader.read(8)
    elif wire_type == WireType.I32:
        value = reader.read(4)
    elif wire_type == WireType.LEN:
        value = reader.read(read_varint(reader))
    else:
        message = "Unknown wire type"
        raise TypeError(message)

    return wire_id, value


def encode_record(data, wire_id: int | None = None) -> bytes:
    if isinstance(data, int):
        if data < 0:
            data = signed_to_zigzag(data)
        return encode_tag(wire_id, WireType.VARINT) + encode_varint(data)

    if isinstance(data, list):
        encoded = b"".join(map(encode_record, data))
    elif isinstance(data, dict):
        encoded = encode(data)
    elif isinstance(data, str):
        encoded = data.encode()
    elif isinstance(data, bytes):
        encoded = data
    else:
        message = f"Unencodable type: {type(data)}"
        raise TypeError(message)

    return encode_tag(wire_id, WireType.LEN) + encode_varint(len(encoded)) + encoded


def read_varint(reader: io.BufferedIOBase):
    shift = 0
    data = 0

    byte = 0b1000_0000
    while byte & 0b1000_0000:
        result = reader.read(1)
        if not result:
            return None
        (byte,) = result
        data |= (byte & 0b0111_1111) << shift
        shift += 7

    return data


def encode_varint(value: int) -> bytes:
    data_length = (value.bit_length() + 6) // 7 or 1
    data = bytearray(data_length)
    for index in range(data_length - 1):
        data[index] = value & 0b0111_1111 | 0b1000_0000
        value >>= 7

    data[-1] = value
    return bytes(data)


def read_tag(reader: io.BufferedIOBase):
    value = read_varint(reader)
    if value is None:
        return None
    return value >> 3, WireType(value & 0b111)


def encode_tag(wire_id: int | None, wire_type: WireType) -> bytes:
    # HACK: easier use in consumer
    if wire_id is None:
        return b""
    return encode_varint((wire_id << 3) | wire_type)


def zigzag_to_signed(value: int):
    result = value >> 1
    if value & 1:
        result = -result - 1
    return result


def signed_to_zigzag(value: int):
    result = value << 1
    if value < 0:
        result = -result - 1
    return result

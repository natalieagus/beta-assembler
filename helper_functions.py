from __future__ import annotations

import beta_32 as beta


def is_number(s):
    if s[:2] == "0b":
        base = 2
    elif s[:2] == "0x":
        base = 16
    elif s.lstrip("-").isnumeric():
        base = 10
    else:
        return False
    try:
        # Have to return a list of the result since '0' will be interpreted as false
        # Goddamn duck typing
        return [int(s, base=base)]
    except ValueError:
        return False


def stoi(x):
    """
    Converts a string to an integer
    - Binary integers should be prefixed with '0b'
    - Hexadecimal integers should be prefixed with '0x'
    - Decimal integers should have no prefix
    """
    if x[:2] == "0b":
        return int(x, 2)
    elif x[:2] == "0x":
        return int(x, 16)
    else:
        return int(x)


def dec_to_hex(x: int) -> str:
    """
    Converts a decimal number to a hexadecimal representation
    """
    return hex(x)[2:].zfill(beta.memory_width // 8)[-(beta.memory_width // 8) :]


def hex_to_dec(x: str) -> int:
    """
    Converts a hexadecimal representation to a decimal number
    """
    if (val := int(x, 16)) > 2 ** (beta.memory_width - 1) - 1:
        # Negative
        return val - 2**beta.memory_width
    else:
        # Positive
        return val


def dec_to_tcbin(x: int) -> str:
    """
    Converts a decimal number to a two's complement binary representation
    """
    if x < 0:
        x = (abs(x) ^ (2**beta.memory_width - 1)) + 1
    return bin(x)[2:].zfill(beta.memory_width)[-beta.memory_width :]


def tcbin_to_dec(x: str) -> int:
    """
    Converts a two's complement binary representation to a decimal number
    """
    if (val := int(x, 2)) > 2 ** (beta.memory_width - 1) - 1:
        # Negative
        return val - 2**beta.memory_width
    else:
        # Positive
        return val


def bit_flip(x: str) -> str:
    """
    Invert the bits of x
    """
    return "".join([("1", "0")[int(i)] for i in x])


def flip(x: int) -> int:
    """
    Convenience function for calling dec_to_tcbin -> bit_flip -> tcbin_to_dec
    """
    return tcbin_to_dec(bit_flip(dec_to_tcbin(x)))

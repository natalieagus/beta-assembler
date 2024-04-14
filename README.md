## Assembler for Beta Assembly

This assembler is made by Alex, a 2024 CSD graduate for his 50.002 1D project. [You can find his github page here](https://github.com/aleextw).

The assembler expects a separate instruction and data memory files. Place your data and instruction inside `./data`. We assume a 32-bit Beta Instruction length, and 16-bit data length. Instruction and data memory are **separated**.

Usage:

```
python assembler_wrapper.py [INPUT_FILENAME] [b|x]
```

1. `[INPUT_FILENAME]` is your `.uasm` file, both DATA and INSTRUCTION must have the SAME name, but the data file to have `_data` suffix
2. `b` stands for binary input, `x` for hex

For instance:

```
python assembler_wrapper.py files/test -b
python assembler_wrapper.py files/test -x
```

We reverse the hex dump because the lowest address is at the bottom for Lucid

Store is TWO cycles because our FPGA RAM requires 2 cycles to write, and make sure it's readable.

## Labels

All labels in instruction and data memory must be put on separate line to be interpreted properly by the assembler. See `./files/test.uasm` and `./files/test_data.uasm` for example.

## System call

SVC(code) is used to assemble system call, where SVC OPCODE is 0x01, and code is embedded in the 16 bit constant. The datapath should handle this.

## Custom instruction

There are also a few custom instructions: `RAND` and `NOP`. The datapath must handle this as well, modify as you wish.

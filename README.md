## Assembler for Beta Assembly

This assembler is made by Alex, a 2024 CSD graduate for his 50.002 1D project. [You can find his github page here](https://github.com/aleextw).

The assembler expects a separate instruction and data memory files. Place your data and instruction inside `./data`

Usage:

```
python assembler_output.py -x ./files/test
```

This will read `./files/test.uasm` (instruction memory) content and `./files/test_data.uasm` (data memory) content, and dump the hex output as `./files/test.hex` and `./files/test_data.hex` accordingly. The file format in the name, `.uasm` is **automatically** added.

We reverse the hex dump because the lowest address is at the bottom for Lucid

Store is TWO cycles because our FPGA RAM requires 2 cycles to write, and make sure it's readable.

For other options:

```
python assembler_output.py -h
```

By default, we use beta_16 (ALU 16 bits). Feel free to change it to beta_32 in `assembler_output` header.

## Labels

All labels in instruction and data memory must be put on separate line to be interpreted properly by the assembler. See `./files/test.uasm` and `./files/test_data.uasm` for example.

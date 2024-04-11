## Assembler for Beta Assembly

This assembler is made by Alex, a 2024 CSD graduate for his 50.002 1D project. [You can find his github page here](https://github.com/aleextw).
Usage:

```
python assembler_output.py -x ./data/test
```

This will read `./data/test.uasm` (instruction memory) content and `./data/test_data.uasm` (data memory) content, and dump the hex output as `./data/test.hex` and `./data/test_data.hex` accordingly. We reverse it because the lowest address is at the bottom for Lucid

Store is TWO cycles because our FPGA RAM requires 2 cycles to write, and make sure it's readable.

For other options:

```
python assembler_output.py -h
```

By default, we use beta_16 (ALU 16 bits). Feel free to change it to beta_32 in `assembler_output` header.

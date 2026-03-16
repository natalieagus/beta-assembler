# Beta Assembler & Simulator for 32-bit Beta CPU

Python assembler and interactive step debugger for the MIT Beta ISA (32-bit). Built for the 50.002 1D project on the Alchitry AU FPGA platform.

The assembler was originally written by Alex, a 2024 CSD graduate. [His GitHub is here](https://github.com/aleextw). The simulator and Tetris board renderer were added on top of his assembler pipeline.

## Project Structure

```
beta-assembler/
├── assembler.py          # Core assembler: .uasm source → binary/hex byte lists
├── assembler_wrapper.py  # CLI wrapper around assembler.py
├── beta_32.py            # Beta ISA definition: instruction encoders, register names
├── helper_functions.py   # Number parsing, two's complement, hex/bin conversion
├── shunting_yard.py      # Expression evaluator (handles labels, arithmetic in .uasm)
└── files/
    ├── game.uasm         # Peg solitaire game instruction memory
    ├── game_data.uasm    # Peg solitaire game data memory
    └── test*.uasm        # Various test programs
```

## Requirements

```
pip install parameterized
```

Python 3.10 or later. The curses-based simulators work on macOS and Linux terminals out of the box. On Windows, use WSL.

## Assembler

### How it works

The assembler translates `.uasm` source files into byte arrays (binary or hex). Instruction and data memory are kept in **separate files**:

- `filename.uasm`: instruction memory
- `filename_data.uasm`: data memory (optional)

The Beta instruction width is **32 bits**. Data memory width is also **32 bits** (`memory_width = 32` in `beta_32.py`), reflecting full 32-bit word addressability on the FPGA.

Labels defined in data memory are passed to the instruction assembler so they can be referenced in `LD`, `ST`, and branch instructions. The assembler runs two passes: the first resolves label addresses, the second emits the final encoding.

### Usage

```bash
cd beta-assembler
python assembler_wrapper.py files/game -b    # binary output
python assembler_wrapper.py files/game -x    # hex output
```

Output files are written alongside the input:

```
files/game.bin/hex         # assembled instruction memory
files/game_data.bin/hex    # assembled data memory
```

The hex dump is written in **reverse address order** (lowest address at the bottom). This matches the Lucid memory initialisation format on the Alchitry AU.

### Syntax

```uasm
| This is a comment (everything after | on a line is ignored)

delay = 1              | Symbolic constant assignment

. = 0x2600             | Set current address (dot)

TETRIS_BOARD:          | Label (must be on its own line)
LONG(0)                | 32-bit word
WORD(0)                | 16-bit word

CMOVE(1, R1)           | Constant-move: R1 = 1
ADDC(R1, 5, R2)        | R2 = R1 + 5
ST(R1, TETRIS_BOARD, R2)   | mem[TETRIS_BOARD + R2] = R1
BEQ(R0, my_label, R31)     | branch if R0 == 0
BR(loop)               | unconditional branch
```

Labels must be placed on their own line. A label followed immediately by an instruction on the same line will not be parsed correctly.

### ISA `beta_32.py`

The ISA is defined in `beta_32.py` as Python lambda functions. All instruction encoders return a list of 8-character binary strings (one per byte, little-endian). Key parameters:

| Parameter           | Value                |
| ------------------- | -------------------- |
| `instruction_width` | 32 bits              |
| `memory_width`      | 32 bits              |
| `output_size`       | 2 hex chars per byte |

**Instruction format** (32 bits):

```
[31:26] opcode   [25:21] RC   [20:16] RA   [15:11] RB (type 1)
                                            [15:0]  CC (type 2, signed 16-bit literal)
```

**Register aliases:**

| Name | Number | Role                           |
| ---- | ------ | ------------------------------ |
| BP   | R27    | Base/frame pointer             |
| LP   | R28    | Link register (return address) |
| SP   | R29    | Stack pointer                  |
| XP   | R30    | Interrupt return pointer       |
| R31  | R31    | Always zero (hardwired)        |

**Instruction set summary:**

| Category   | Instructions                                |
| ---------- | ------------------------------------------- |
| Arithmetic | ADD, ADDC, SUB, SUBC, MUL, MULC, DIV, DIVC  |
| Logic      | AND, ANDC, OR, ORC, XOR, XORC, XNOR, XNORC  |
| Shift      | SHL, SHLC, SHR, SHRC, SRA, SRAC             |
| Compare    | CMPEQ, CMPEQC, CMPLE, CMPLEC, CMPLT, CMPLTC |
| Branch     | BEQ / BF, BNE / BT, BR, JMP                 |
| Memory     | LD, ST, LDR                                 |
| Pseudo     | MOVE, CMOVE, PUSH, POP, CALL, RTN, XRTN     |
| Data       | WORD, LONG, STORAGE                         |
| System     | HALT, SVC(code), RAND, NOP                  |

**System call:** `SVC(code)` has opcode `0x01`. The code is embedded in the 16-bit constant field. The datapath is responsible for handling the trap.

**Custom instructions:** `RAND` (opcode `0x03`) and `NOP` (opcode `0x02`) are non-standard extensions. The datapath must implement them — modify as needed for your design.

**Labels** must always be placed on their own line. A label followed by an instruction on the same line will not be parsed correctly. See `files/test.uasm` and `files/test_data.uasm` for working examples.

## Notes

- The hex output is **reversed** relative to address order to match Lucid's `$readmemh` format on the Alchitry AU.
- `beta_32.py` is the authoritative ISA definition. Do NOT hardcode opcode values anywhere else, always derive them from `beta_32` by encoding a test instruction and reading back the opcode field.

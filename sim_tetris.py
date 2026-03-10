#!/usr/bin/env python3
"""
Beta CPU Simulator Showing Tetris Board
Uses the project's assembler.py + beta_32.py. Opcodes are read
directly from beta_32 at startup so they stay in sync automatically.

Board: 22 rows x 12 columns at label TETRIS_BOARD (0x2600)
       Each cell is one LONG (4 bytes, little-endian 32-bit).
       Col 0 and col 11 are pre-filled walls.

Usage:
    cd beta-assembler
    python sim_tetris.py files/tetris

Keys:
    n   step one instruction
    r   run until breakpoint / HALT
    b   toggle breakpoint at current PC
    c   clear all breakpoints
    R   reset (PC=0, restore original data memory)
    q   quit
"""

import sys, os, curses, random, io, contextlib

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import beta_32 as beta                        # project ISA definition
from assembler import parse_asm_file          # project assembler

# Encode a dummy instruction and extract bits [31:26] to get the opcode.
def _op(encoded_bytes):
    """Return the 6-bit opcode from the first 4 bytes of an encoded instruction."""
    w = sum(int(encoded_bytes[j], 2) << (8 * j) for j in range(4))
    return (w >> 26) & 0x3F

# Save / restore beta.dot so we don't corrupt a real assembly session
_dot_save = beta.dot
beta.dot = 0

OP_ADD   = _op(beta.ADD  (0, 1, 2));   OP_ADDC  = _op(beta.ADDC (0, 1, 2))
OP_SUB   = _op(beta.SUB  (0, 1, 2));   OP_SUBC  = _op(beta.SUBC (0, 1, 2))
OP_MUL   = _op(beta.MUL  (0, 1, 2));   OP_MULC  = _op(beta.MULC (0, 1, 2))
OP_DIV   = _op(beta.DIV  (0, 1, 2));   OP_DIVC  = _op(beta.DIVC (0, 1, 2))
OP_AND   = _op(beta.AND  (0, 1, 2));   OP_ANDC  = _op(beta.ANDC (0, 1, 2))
OP_OR    = _op(beta.OR   (0, 1, 2));   OP_ORC   = _op(beta.ORC  (0, 1, 2))
OP_XOR   = _op(beta.XOR  (0, 1, 2));   OP_XORC  = _op(beta.XORC (0, 1, 2))
OP_XNOR  = _op(beta.XNOR (0, 1, 2));   OP_XNORC = _op(beta.XNORC(0, 1, 2))
OP_SHL   = _op(beta.SHL  (0, 1, 2));   OP_SHLC  = _op(beta.SHLC (0, 1, 2))
OP_SHR   = _op(beta.SHR  (0, 1, 2));   OP_SHRC  = _op(beta.SHRC (0, 1, 2))
OP_SRA   = _op(beta.SRA  (0, 1, 2));   OP_SRAC  = _op(beta.SRAC (0, 1, 2))
OP_CMPEQ = _op(beta.CMPEQ(0, 1, 2));   OP_CMPEQC= _op(beta.CMPEQC(0,1,2))
OP_CMPLE = _op(beta.CMPLE(0, 1, 2));   OP_CMPLEC= _op(beta.CMPLEC(0,1,2))
OP_CMPLT = _op(beta.CMPLT(0, 1, 2));   OP_CMPLTC= _op(beta.CMPLTC(0,1,2))
OP_NOP   = _op(beta.NOP())
OP_HALT  = _op(beta.HALT())
OP_SVC   = _op(beta.SVC(0))
OP_RAND  = _op(beta.RAND(0))
OP_BEQ   = _op(beta.BEQ(0, 4, 31))     # label=dot+4 gives offset=0
OP_BNE   = _op(beta.BNE(0, 4, 31))
OP_JMP   = _op(beta.JMP(0, 31))
OP_LD    = _op(beta.LD(0, 0, 1)[:4])   # LD is doubled; take first 4 bytes
OP_ST    = _op(beta.ST(1, 0, 0)[:4])   # ST is doubled; take first 4 bytes
OP_LDR   = _op(beta.LDR(4, 0))         # LDR(label, RC) with label=dot+4

beta.dot = _dot_save                    # restore

OP_NAMES = {
    OP_ADD:'ADD',   OP_ADDC:'ADDC',  OP_SUB:'SUB',    OP_SUBC:'SUBC',
    OP_MUL:'MUL',   OP_MULC:'MULC',  OP_DIV:'DIV',    OP_DIVC:'DIVC',
    OP_AND:'AND',   OP_ANDC:'ANDC',  OP_OR:'OR',       OP_ORC:'ORC',
    OP_XOR:'XOR',   OP_XORC:'XORC', OP_XNOR:'XNOR',   OP_XNORC:'XNORC',
    OP_SHL:'SHL',   OP_SHLC:'SHLC', OP_SHR:'SHR',     OP_SHRC:'SHRC',
    OP_SRA:'SRA',   OP_SRAC:'SRAC',
    OP_CMPEQ:'CMPEQ',  OP_CMPEQC:'CMPEQC',
    OP_CMPLE:'CMPLE',  OP_CMPLEC:'CMPLEC',
    OP_CMPLT:'CMPLT',  OP_CMPLTC:'CMPLTC',
    OP_NOP:'NOP',   OP_HALT:'HALT', OP_SVC:'SVC',      OP_RAND:'RAND',
    OP_BEQ:'BEQ',   OP_BNE:'BNE',  OP_JMP:'JMP',
    OP_LD:'LD',     OP_ST:'ST',    OP_LDR:'LDR',
}

REG_ALIAS = {27: 'BP', 28: 'LP', 29: 'SP', 30: 'XP', 31: 'ZR'}

# board layout 
BOARD_ROWS  = 22
BOARD_COLS  = 12
BOARD_LABEL = 'TETRIS_BOARD'    # data label looked up at runtime

# arithmetic helpers 
def sext16(v): v &= 0xFFFF;     return v - 0x10000     if v & 0x8000     else v
def sext32(v): v &= 0xFFFFFFFF; return v - 0x100000000 if v & 0x80000000 else v
def u32(v):    return v & 0xFFFFFFFF


# simulator 
class BetaSim:
    """
    A simple terminal UI that executes Beta ISA programs produced by the project assembler.
    Memory is 32-bit (matching beta_32.memory_width).
    LD/ST are 32-bit operations (beta_32 uses LONG-sized cells).
    LD and ST are encoded twice by the assembler (FPGA 2-cycle pipeline)
    the simulator detects the duplicate and skips it automatically.
    """

    def __init__(self, ibytes, dbytes, ilabels, dlabels):
        # ibytes / dbytes: lists of 8-char binary strings (one per byte)
        # Reconstruct 32-bit little-endian instruction words
        self.imem = []
        for i in range(0, len(ibytes), 4):
            w = sum(int(ibytes[i + j], 2) << (8 * j)
                    for j in range(min(4, len(ibytes) - i)))
            self.imem.append(w)

        # Data memory: writable bytearray
        raw = bytes(int(b, 2) for b in dbytes)
        size = max(len(raw), 0x3000)
        self.dmem = bytearray(size)
        self.dmem[:len(raw)] = raw
        self._dmem_init = bytes(self.dmem)

        self.regs        = [0] * 32
        self.pc          = 0
        self.cycles      = 0
        self.halted      = False
        self.stop_reason = ''
        self.last_op     = 'ready'
        self.breakpoints: set = set()

        self.ilabels   = ilabels or {}
        self.dlabels   = dlabels or {}
        self.iaddr2lbl = {v: k for k, v in self.ilabels.items()}
        self.daddr2lbl = {v: k for k, v in self.dlabels.items()}

    def reset(self):
        self.regs        = [0] * 32
        self.pc          = 0
        self.cycles      = 0
        self.halted      = False
        self.stop_reason = ''
        self.last_op     = 'reset'
        self.dmem        = bytearray(self._dmem_init)

    # memory (32-bit, little-endian) 
    def read32(self, addr):
        a = addr & ~3
        if a + 4 > len(self.dmem):
            return 0
        return (self.dmem[a]
                | self.dmem[a+1] << 8
                | self.dmem[a+2] << 16
                | self.dmem[a+3] << 24)

    def write32(self, addr, val):
        a   = addr & ~3
        val = val & 0xFFFFFFFF
        if a + 4 > len(self.dmem):
            self.dmem.extend(bytes(a + 4 - len(self.dmem) + 256))
        self.dmem[a]   =  val        & 0xFF
        self.dmem[a+1] = (val >>  8) & 0xFF
        self.dmem[a+2] = (val >> 16) & 0xFF
        self.dmem[a+3] = (val >> 24) & 0xFF

    # registers 
    def rget(self, r): return 0 if r == 31 else self.regs[r]
    def rset(self, r, v):
        if r != 31:
            self.regs[r] = sext32(v)

    # fetch 
    def fetch(self, addr=None):
        idx = (self.pc if addr is None else addr) >> 2
        return self.imem[idx] if 0 <= idx < len(self.imem) else None

    # execute one instruction 
    def step(self):
        if self.halted:
            return False

        w = self.fetch()
        if w is None:
            self.halted      = True
            self.stop_reason = 'PC out of instruction memory'
            return False

        op  = (w >> 26) & 0x3F
        rc  = (w >> 21) & 0x1F
        ra  = (w >> 16) & 0x1F
        rb  = (w >> 11) & 0x1F
        lit = sext16(w & 0xFFFF)
        av  = self.rget(ra)
        bv  = self.rget(rb)
        pc  = self.pc
        npc = pc + 4

        # ALU 
        if   op == OP_ADD:    self.rset(rc, av + bv)
        elif op == OP_ADDC:   self.rset(rc, av + lit)
        elif op == OP_SUB:    self.rset(rc, av - bv)
        elif op == OP_SUBC:   self.rset(rc, av - lit)
        elif op == OP_MUL:    self.rset(rc, av * bv)
        elif op == OP_MULC:   self.rset(rc, av * lit)
        elif op == OP_DIV:    self.rset(rc, sext32(av) // sext32(bv) if bv else 0)
        elif op == OP_DIVC:   self.rset(rc, sext32(av) // lit        if lit else 0)
        elif op == OP_AND:    self.rset(rc, av & bv)
        elif op == OP_ANDC:   self.rset(rc, av & lit)
        elif op == OP_OR:     self.rset(rc, av | bv)
        elif op == OP_ORC:    self.rset(rc, av | lit)
        elif op == OP_XOR:    self.rset(rc, av ^ bv)
        elif op == OP_XORC:   self.rset(rc, av ^ lit)
        elif op == OP_XNOR:   self.rset(rc, ~(av ^ bv))
        elif op == OP_XNORC:  self.rset(rc, ~(av ^ lit))
        elif op == OP_SHL:    self.rset(rc, u32(av) << (bv  & 0x1F))
        elif op == OP_SHLC:   self.rset(rc, u32(av) << (lit & 0x1F))
        elif op == OP_SHR:    self.rset(rc, u32(av) >> (bv  & 0x1F))
        elif op == OP_SHRC:   self.rset(rc, u32(av) >> (lit & 0x1F))
        elif op == OP_SRA:    self.rset(rc, sext32(av) >> (bv  & 0x1F))
        elif op == OP_SRAC:   self.rset(rc, sext32(av) >> (lit & 0x1F))
        elif op == OP_CMPEQ:  self.rset(rc, 1 if av == bv  else 0)
        elif op == OP_CMPEQC: self.rset(rc, 1 if av == lit else 0)
        elif op == OP_CMPLE:  self.rset(rc, 1 if sext32(av) <= sext32(bv) else 0)
        elif op == OP_CMPLEC: self.rset(rc, 1 if sext32(av) <= lit        else 0)
        elif op == OP_CMPLT:  self.rset(rc, 1 if sext32(av) <  sext32(bv) else 0)
        elif op == OP_CMPLTC: self.rset(rc, 1 if sext32(av) <  lit        else 0)
        elif op == OP_RAND:   self.rset(0, random.randint(0, 0xFFFFFFFF))
        elif op == OP_NOP:    pass

        # branches 
        elif op in (OP_BEQ, OP_BNE):
            self.rset(rc, pc + 4)
            taken = (av == 0) if op == OP_BEQ else (av != 0)
            if taken:
                npc = pc + 4 * (lit + 1)
        elif op == OP_JMP:
            self.rset(rc, pc + 4)
            npc = av & ~3
        elif op == OP_LDR:
            # PC-relative load: effective addr = PC + 4*(lit+1)
            eff = pc + 4 * (lit + 1)
            self.rset(rc, self.read32(eff))

        # memory 
        elif op == OP_LD:
            self.rset(rc, self.read32(av + lit))
            # assembler encodes LD twice; skip duplicate
            if self.fetch(pc + 4) == w:
                npc = pc + 8
        elif op == OP_ST:
            self.write32(av + lit, self.rget(rc))
            # assembler encodes ST twice; skip duplicate
            if self.fetch(pc + 4) == w:
                npc = pc + 8

        # system 
        elif op == OP_HALT:
            self.halted      = True
            self.stop_reason = 'HALT'
            self.last_op     = 'HALT()'
            return False
        elif op == OP_SVC:
            # No keyboard in this sim; treat SVC as NOP
            pass
        else:
            self.stop_reason = f'unknown opcode 0x{op:02x} at PC 0x{pc:04X}'

        self.pc       = npc
        self.regs[31] = 0
        self.cycles  += 1
        self.last_op  = self.disasm(pc)
        return True

    def run_to_break(self, limit=2_000_000):
        first = True
        for _ in range(limit):
            if self.halted:
                return
            if not first and self.pc in self.breakpoints:
                self.stop_reason = f'breakpoint @ 0x{self.pc:04X}'
                return
            first = False
            if not self.step():
                return
        self.stop_reason = 'step limit reached'

    # disassembler 
    def disasm(self, addr):
        w = self.fetch(addr)
        if w is None:
            return '???'

        op   = (w >> 26) & 0x3F
        rc   = (w >> 21) & 0x1F
        ra   = (w >> 16) & 0x1F
        rb   = (w >> 11) & 0x1F
        lit  = sext16(w & 0xFFFF)
        name = OP_NAMES.get(op, f'op{op:02x}')

        def rn(r): return REG_ALIAS.get(r, f'R{r}')

        if op == OP_NOP:   return 'NOP()'
        if op == OP_HALT:  return 'HALT()'
        if op == OP_SVC:   return f'SVC({lit})'
        if op == OP_RAND:  return f'RAND({rn(ra)})'
        if op == OP_JMP:
            tail = f', {rn(rc)}' if rc != 31 else ''
            return f'JMP({rn(ra)}{tail})'
        if op in (OP_BEQ, OP_BNE):
            tgt = addr + 4 * (lit + 1)
            lbl = self.iaddr2lbl.get(tgt, f'0x{tgt:04X}')
            if op == OP_BEQ:
                if ra == 31: return f'BR({lbl})'
                tail = f', {rn(rc)}' if rc != 31 else ''
                return f'BF({rn(ra)}, {lbl}{tail})'
            else:
                tail = f', {rn(rc)}' if rc != 31 else ''
                return f'BT({rn(ra)}, {lbl}{tail})'
        if op == OP_LDR:
            tgt = addr + 4 * (lit + 1)
            lbl = self.iaddr2lbl.get(tgt) or self.daddr2lbl.get(tgt) or f'0x{tgt:04X}'
            return f'LDR({lbl}, {rn(rc)})'
        if op == OP_LD:
            lbl = self.daddr2lbl.get(lit & 0xFFFF, f'0x{lit & 0xFFFF:04X}')
            return f'LD({rn(ra)}, {lbl}, {rn(rc)})'
        if op == OP_ST:
            lbl = self.daddr2lbl.get(lit & 0xFFFF, f'0x{lit & 0xFFFF:04X}')
            return f'ST({rn(rc)}, {lbl}, {rn(ra)})'
        if op == OP_ADDC and ra == 31: return f'CMOVE({lit}, {rn(rc)})'
        if op == OP_ADD  and rb == 31: return f'MOVE({rn(ra)}, {rn(rc)})'
        # constant-field variant: bit 4 of op set
        if op & 0x10:
            return f'{name}({rn(ra)}, {lit}, {rn(rc)})'
        return f'{name}({rn(ra)}, {rn(rb)}, {rn(rc)})'


# curses colour pairs 
CP_HDR  = 1   # cyan
CP_REG  = 2   # green
CP_CUR  = 3   # black on cyan  (current PC)
CP_BP   = 4   # red            (breakpoint)
CP_WALL = 5   # yellow bold    (wall cells)
CP_FILL = 6   # green bold     (filled cells)
CP_CTRL = 7   # bold           (control bar)

def _init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_HDR,  curses.COLOR_CYAN,   -1)
    curses.init_pair(CP_REG,  curses.COLOR_GREEN,  -1)
    curses.init_pair(CP_CUR,  curses.COLOR_BLACK,  curses.COLOR_CYAN)
    curses.init_pair(CP_BP,   curses.COLOR_RED,    -1)
    curses.init_pair(CP_WALL, curses.COLOR_YELLOW, -1)
    curses.init_pair(CP_FILL, curses.COLOR_GREEN,  -1)
    curses.init_pair(CP_CTRL, curses.COLOR_CYAN,   -1)

def _put(win, y, x, s, attr=0):
    H, W = win.getmaxyx()
    if y < 0 or y >= H - 1 or x < 0 or x >= W:
        return
    try:
        win.addstr(y, x, s[:W - x - 1], attr)
    except curses.error:
        pass

def _sep(win, y, label=''):
    H, W = win.getmaxyx()
    if y < 0 or y >= H - 1:
        return
    tag  = f' {label} ' if label else ''
    mid  = (W - len(tag)) // 2
    line = '─' * W
    if tag:
        line = line[:mid] + tag + line[mid + len(tag):]
    _put(win, y, 0, line, curses.color_pair(CP_HDR))


# board drawing 
#
# Layout on screen:
#   Board is drawn at the LEFT (col 0 of terminal).
#   Each board column is 2 terminal chars wide (glyphs below).
#   Registers are drawn to the RIGHT of the board.
#
# Glyph key:
#   wall  -> '##'  yellow bold
#   filled-> '[]'  green bold
#   empty -> '  '

GLYPH_WALL  = '##'
GLYPH_FILL  = '[]'
GLYPH_EMPTY = '  '

def _draw_board(win, sim: BetaSim, term_row: int, term_col: int) -> int:
    """Draw the 22-row x 12-col board. Returns the terminal row below it."""
    H, W = win.getmaxyx()

    base = sim.dlabels.get(BOARD_LABEL)
    if base is None:
        _put(win, term_row, term_col,
             f'[{BOARD_LABEL} label not found]', curses.color_pair(CP_BP))
        return term_row + 1

    # Column header
    hdr = '   '
    for c in range(BOARD_COLS):
        hdr += f'{c:<2d}'
    _put(win, term_row, term_col, hdr, curses.color_pair(CP_HDR))
    term_row += 1

    for r in range(BOARD_ROWS):
        if term_row >= H - 1:
            break
        x = term_col
        # Row label
        label_str = f'{r:2d} '
        _put(win, term_row, x, label_str, curses.color_pair(CP_HDR))
        x += len(label_str)

        for c in range(BOARD_COLS):
            cell_addr = base + (r * BOARD_COLS + c) * 4
            val       = sim.read32(cell_addr)
            is_wall   = (c == 0 or c == BOARD_COLS - 1)

            if is_wall:
                _put(win, term_row, x, GLYPH_WALL,
                     curses.color_pair(CP_WALL) | curses.A_BOLD)
            elif val:
                _put(win, term_row, x, GLYPH_FILL,
                     curses.color_pair(CP_FILL) | curses.A_BOLD)
            else:
                _put(win, term_row, x, GLYPH_EMPTY)
            x += 2

        term_row += 1

    return term_row


# main render 
def render(win, sim: BetaSim):
    win.erase()
    H, W = win.getmaxyx()

    # title bar 
    pc_lbl = sim.iaddr2lbl.get(sim.pc, '')
    pc_str = f'0x{sim.pc:04X}' + (f'({pc_lbl})' if pc_lbl else '')
    state  = 'HALTED' if sim.halted else 'RUNNING'
    bp_s   = ('  BP:' + ','.join(f'0x{b:04X}' for b in sorted(sim.breakpoints)[:4])
               if sim.breakpoints else '')
    title  = f'  TETRIS SIM   PC:{pc_str}   cycles:{sim.cycles:,}   [{state}]{bp_s}'
    _put(win, 0, 0, title, curses.color_pair(CP_HDR) | curses.A_BOLD)

    # board (left column) 
    BOARD_TERM_COL = 0
    # board width in terminal chars: 3 (label) + BOARD_COLS * 2
    BOARD_TERM_W   = 3 + BOARD_COLS * 2   # = 27 chars

    base_addr = sim.dlabels.get(BOARD_LABEL, 0)
    board_hdr = (f' {BOARD_LABEL} @0x{base_addr:04X}'
                 f'  {BOARD_ROWS}r x {BOARD_COLS}c  32b/cell')
    _put(win, 1, BOARD_TERM_COL, board_hdr, curses.color_pair(CP_HDR))

    board_end_row = _draw_board(win, sim, 2, BOARD_TERM_COL)

    # registers (right of board)
    REG_COL = BOARD_TERM_W + 2
    reg_row  = 1
    _put(win, reg_row, REG_COL, 'REGISTERS',
         curses.color_pair(CP_HDR) | curses.A_BOLD)
    reg_row += 1

    for r in range(32):
        if reg_row >= H - 2:
            break
        alias = REG_ALIAS.get(r, '')
        tag   = f'R{r}/{alias}' if alias else f'R{r}   '
        val   = sim.regs[r]
        text  = f'{tag:<6s}:{val:#010x}'
        _put(win, reg_row, REG_COL, text, curses.color_pair(CP_REG))
        reg_row += 1

    # disassembly (below registers if space, else below board) 
    da_start = max(board_end_row, reg_row) + 1
    if da_start < H - 3:
        _sep(win, da_start - 1, 'DISASSEMBLY')
        CONTEXT = min(5, H - da_start - 2)
        half    = CONTEXT // 2
        start   = max(0, ((sim.pc >> 2) - half) << 2)

        for i in range(CONTEXT):
            row = da_start + i
            if row >= H - 2:
                break
            addr   = start + i * 4
            is_cur = (addr == sim.pc)
            is_bp  = (addr in sim.breakpoints)
            lbl    = sim.iaddr2lbl.get(addr, '')
            da     = sim.disasm(addr)
            pfx    = '► ' if is_cur else ('● ' if is_bp else '  ')
            lbl_s  = f'{lbl}:' if lbl else ''
            line   = f'{pfx}0x{addr:04X}  {lbl_s:<12s}{da}'

            if is_cur:  attr = curses.color_pair(CP_CUR) | curses.A_BOLD
            elif is_bp: attr = curses.color_pair(CP_BP)
            else:        attr = 0
            _put(win, row, 0, line, attr)

    # status + controls 
    st = sim.last_op
    if sim.stop_reason:
        st = f'{sim.stop_reason}  |  {st}'
    _put(win, H - 2, 0, st[:W - 1])
    ctrl = '  [n]step  [r]run  [b]BP@PC  [c]clear-BP  [R]reset  [q]quit'
    _put(win, H - 1, 0, ctrl, curses.color_pair(CP_CTRL) | curses.A_BOLD)

    win.refresh()


# event loop 
def run_ui(stdscr, sim: BetaSim):
    curses.curs_set(0)
    stdscr.keypad(True)
    _init_colors()

    while True:
        render(stdscr, sim)
        key = stdscr.getch()

        if key in (ord('q'), ord('Q')):
            break
        elif key == ord('n'):
            if not sim.halted:
                sim.step()
        elif key == ord('r'):
            if not sim.halted:
                sim.run_to_break()
        elif key == ord('b'):
            if sim.pc in sim.breakpoints:
                sim.breakpoints.discard(sim.pc)
            else:
                sim.breakpoints.add(sim.pc)
        elif key in (ord('c'), ord('C')):
            sim.breakpoints.clear()
        elif key == ord('R'):
            sim.reset()


# assembly loader 
def assemble(base: str):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        data_mem, data_labels = parse_asm_file(
            input_filename  = f'{base}_data.uasm',
            output_filename = f'{base}_data.bin',
            existing_labels = None,
            input_format    = 'data',
            output_format   = 'bin',
        )
        if data_mem is None:
            data_mem, data_labels = [], {}

        instr_mem, instr_labels = parse_asm_file(
            input_filename  = f'{base}.uasm',
            output_filename = f'{base}.bin',
            existing_labels = data_labels,
            input_format    = 'instr',
            output_format   = 'bin',
        )

    if instr_mem is None:
        return None, f'ERROR: cannot assemble {base}.uasm'

    return BetaSim(instr_mem, data_mem, instr_labels, data_labels), None


# entry point 
def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'files/tetris'

    sim, err = assemble(base)
    if err:
        print(err)
        sys.exit(1)

    board_addr = sim.dlabels.get(BOARD_LABEL)
    print('Assembled OK')
    print(f'  ISA        : beta_32 (memory_width={beta.memory_width})')
    print(f'  data       : {len(sim.dmem)} bytes')
    print(f'  instr      : {len(sim.imem) * 4} bytes  ({len(sim.imem)} words)')
    print(f'  {BOARD_LABEL} @ {hex(board_addr) if board_addr is not None else "NOT FOUND"}')
    print(f'  board      : {BOARD_ROWS} rows x {BOARD_COLS} cols'
          f'  ({BOARD_ROWS * BOARD_COLS} cells x 4 B = {BOARD_ROWS * BOARD_COLS * 4} B)')
    print()

    curses.wrapper(lambda scr: run_ui(scr, sim))


if __name__ == '__main__':
    main()

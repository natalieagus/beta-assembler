########################################################################
### 50.002 BETA Macro package -                  revised 9/28/11 SAW  ###
###  This file defines our 32-bit Beta instruction set.              ###
########################################################################

# Global instruction definition conventions:
#  * DESTINATION arg is LAST

# Instruction set summary.  Notation:
# ra, rb, rc: registers
#         CC: 16-bit signed constant
#      label: statement/location tag (becomes PC-relative offset)

# ADD(RA, RB, RC)       # RC <- <RA> + <RB>
# ADDC(RA, C, RC)       # RC <- <RA> + C
# AND(RA, RB, RC)       # RC <- <RA> & <RB>
# ANDC(RA, C, RC)       # RC <- <RA> & C
# MUL(RA, RB, RC)       # RC <- <RA> * <RB>
# MULC(RA, C, RC)       # RC <- <RA> * C
# DIV(RA, RB, RC)       # RC <- <RA> / <RB>
# DIVC(RA, C, RC)       # RC <- <RA> / C
# OR( RA, RB, RC)       # RC <- <RA> # <RB>
# ORC(RA,  C, RC)       # RC <- <RA> # C
# SHL(RA, RB, RC)       # RC <- <RA> << <RB>
# SHLC(RA, C, RC)       # RC <- <RA> << C
# SHR(RA, RB, RC)       # RC <- <RA> >> <RB>
# SHRC(RA, C, RC)       # RC <- <RA> >> C
# SRA(RA, RB, RC)       # RC <- <RA> >> <RB>
# SRAC(RA, C, RC)       # RC <- <RA> >> C
# SUB(RA, RB, RC)       # RC <- <RA> - <RB>
# SUBC(RA, C, RC)       # RC <- <RA> - C
# XOR(RA, RB, RC)       # RC <- <RA> ^ <RB>
# XORC(RA, C, RC)       # RC <- <RA> ^ C
# XNOR(RA, RB, RC)      # RC <- ~(<RA> ^ <RB>)
# XNORC(RA, C, RC)      # RC <- ~(<RA> ^ C)

# CMPEQ(RA, RB, RC)     # RC <- <RA> == <RB>
# CMPEQC(RA, C, RC)     # RC <- <RA> == C
# CMPLE(RA, RB, RC)     # RC <- <RA> <= <RB>
# CMPLEC(RA, C, RC)     # RC <- <RA> <= C
# CMPLT(RA, RB, RC)     # RC <- <RA> <  <RB>
# CMPLTC(RA, C, RC)     # RC <- <RA> <  C


# BR(LABEL,RC)          # RC <- <PC>+4; PC <- LABEL (PC-relative addressing)
# BR(LABEL)             # PC <- LABEL (PC-relative addressing)
# BEQ(RA, LABEL, RC)    # RC <- <PC>+4; IF <RA>==0 THEN PC <- LABEL
# BEQ(RA, LABEL)        # IF <RA>==0 THEN PC <- LABEL
# BF(RA, LABEL, RC)     # RC <- <PC>+4; IF <RA>==0 THEN PC <- LABEL
# BF(RA, LABEL)         # IF <RA>==0 THEN PC <- LABEL
# BNE(RA, LABEL, RC)    # RC <- <PC>+4; IF <RA>!=0 THEN PC <- LABEL
# BNE(RA, LABEL)        # IF <RA>!=0 THEN PC <- LABEL
# BT(RA, LABEL, RC)     # RC <- <PC>+4; IF <RA>!=0 THEN PC <- LABEL
# BT(RA, LABEL)         # IF <RA>!=0 THEN PC <- LABEL
# JMP(RA, RC)           # RC <- <PC>+4; PC <- <RA> & 0xFFFC
# JMP(RB)               # PC <- <RB> & 0xFFFC

# LD(RA, CC, RC)        # RC <- <<RA>+CC>
# LD(CC, RC)            # RC <- <CC>
# ST(RC, CC, RA)        # <RA>+CC <- <RC>
# ST(RC, CC)            # CC <- <RC>
# LDR(CC, RC)           # RC <- <CC> (PC-relative addressing)

# MOVE(RA, RC)          # RC <- <RA>
# CMOVE(CC, RC)         # RC <- CC
# HALT()                # STOPS SIMULATOR.

# PUSH(RA)              # (2) <SP> <- <RA>; SP <- <SP> - 4
# POP(RA)               # (2) RA <- <<SP>+4>; SP <- <SP> + 4
# ALLOCATE(N)           # Allocate N longwords from stack
# DEALLOCATE(N)         # Release N longwords

# CALL(label)           # Call a subr; save PC in lp.
# CALL(label, n)        # (2) Call subr at label with n args.
# Saves return adr in LP.
# Pops n longword args from stack.

# RTN()                 # Returns to adr in <LP> (Subr return)
# XRTN()                # Returns to adr in <IP> (Intr return)

# WORD(val)             # Assemble val as a 16-bit datum
# LONG(val)             # Assemble val as a 32-bit datum
# STORAGE(NWORDS)       # Reserve NWORDS 32-bit words of DRAM

# GETFRAME(F, RA)       # RA <- <<BP>+F>
# PUTFRAME(RA, F)       # <BP>+F <- <RA>

# Calling convention:
#       PUSH(argn-1)
#       ...
#       PUSH(arg0)
#       CALL(subr, nargs)
#       (return here with result in R0, args cleaned)

# Extra register conventions, for procedure linkage:
# LP = 28                       # Linkage register (holds return adr)
# BP = 29                       # Frame pointer (points to base of frame)

# Conventional stack frames look like:
#       arg[N-1]
#       ...
#       arg[0]
#       <saved lp>
#       <saved bp>
#       <other saved regs>
#   BP-><locals>
#       ...
#   SP->(first unused location)

# Convention: define a symbol for each arg/local giving bp-relative offset.
# Then use
#   getframe(name, r) gets value at offset into register r.
#   putframe(r, name) puts value from r into frame at offset name


########################################################################
### End of documentation.  Following are the actual definitions...   ###
########################################################################

# var storing current instruction address
dot = 0

# var storing output formatter func
output_func = bin
output_size = 2

# Instruction and memory size in bits
instruction_width = 32
memory_width = 16 

# register designators
# this allows symbols like r0, etc to be used as
# operands in instructions. Note that there is no real difference
# in this assembler between register operands and small integers.
r0 = 0
r1 = 1
r2 = 2
r3 = 3
r4 = 4
r5 = 5
r6 = 6
r7 = 7
r8 = 8
r9 = 9
r10 = 10
r11 = 11
r12 = 12
r13 = 13
r14 = 14
r15 = 15
r16 = 16
r17 = 17
r18 = 18
r19 = 19
r20 = 20
r21 = 21
r22 = 22
r23 = 23
r24 = 24
r25 = 25
r26 = 26
r27 = 27
r28 = 28
r29 = 29
r30 = 30
r31 = 31

bp = 27  # frame pointer (points to base of frame)
lp = 28  # linkage register (holds return adr)
sp = 29  # stack pointer (points to 1st free locn)
xp = 30  # interrupt return pointer (lp for interrupts)

# understand upper case, too.
R0 = r0
R1 = r1
R2 = r2
R3 = r3
R4 = r4
R5 = r5
R6 = r6
R7 = r7
R8 = r8
R9 = r9
R10 = r10
R11 = r11
R12 = r12
R13 = r13
R14 = r14
R15 = r15
R16 = r16
R17 = r17
R18 = r18
R19 = r19
R20 = r20
R21 = r21
R22 = r22
R23 = r23
R24 = r24
R25 = r25
R26 = r26
R27 = r27
R28 = r28
R29 = r29
R30 = r30
R31 = r31
XP = xp
LP = lp
BP = bp
SP = sp

# Trap and interrupt vectors
VEC_RESET = 0  # Reset (powerup)
VEC_II = 4  # Illegal instruction (also SVC call)
VEC_CLK = 8  # Clock interrupt
VEC_KBD = 12  # Keyboard interrupt
VEC_MOUSE = 16  # Mouse interrupt

# constant for the supervisor bit in the PC
PC_SUPERVISOR = 0x80000000  # the bit itself
PC_MASK = 0x7FFFFFFFF  # a mask for the rest of the PC


def WORD(x):
    return [output_func((x % 0x100))[2:].zfill(output_size)] + [
        output_func((x >> 8) % 0x100)[2:].zfill(output_size)
    ]
    # return list(hex(((x % 0x100) << 8) + ((x >> 8) % 0x100))[2:].zfill(4))


def LONG(x):
    # Return 32-bit byte array (in hex)
    return WORD(x) + WORD(x >> 16)


def STORAGE(NWORDS):
    global dot
    dot += 4 * NWORDS


def betaop(OP, RA, RB, RC):
    align(4)
    # LONG() will convert to little-endian
    # If we want big-endian, return the arg instead
    return LONG(
        (OP << 26) + ((RC % 0x20) << 21) + ((RA % 0x20) << 16) + ((RB % 0x20) << 11)
    )


def betaopc(OP, RA, CC, RC):
    align(4)
    # LONG() will convert to little-endian
    # If we want big-endian, return the arg instead
    return LONG((OP << 26) + ((RC % 0x20) << 21) + ((RA % 0x20) << 16) + (CC % 0x10000))


def align(x=4):
    global dot
    dot = ((dot - 1) // x + 1) * x


ADD = lambda RA, RB, RC: betaop(0x20, RA, RB, RC)
ADDC = lambda RA, C, RC: betaopc(0x30, RA, C, RC)
AND = lambda RA, RB, RC: betaop(0x28, RA, RB, RC)
ANDC = lambda RA, C, RC: betaopc(0x38, RA, C, RC)
MUL = lambda RA, RB, RC: betaop(0x22, RA, RB, RC)
MULC = lambda RA, C, RC: betaopc(0x32, RA, C, RC)
DIV = lambda RA, RB, RC: betaop(0x23, RA, RB, RC)
DIVC = lambda RA, C, RC: betaopc(0x33, RA, C, RC)
OR = lambda RA, RB, RC: betaop(0x29, RA, RB, RC)
ORC = lambda RA, C, RC: betaopc(0x39, RA, C, RC)
SHL = lambda RA, RB, RC: betaop(0x2C, RA, RB, RC)
SHLC = lambda RA, C, RC: betaopc(0x3C, RA, C, RC)
SHR = lambda RA, RB, RC: betaop(0x2D, RA, RB, RC)
SHRC = lambda RA, C, RC: betaopc(0x3D, RA, C, RC)
SRA = lambda RA, RB, RC: betaop(0x2E, RA, RB, RC)
SRAC = lambda RA, C, RC: betaopc(0x3E, RA, C, RC)
SUB = lambda RA, RB, RC: betaop(0x21, RA, RB, RC)
SUBC = lambda RA, C, RC: betaopc(0x31, RA, C, RC)
XOR = lambda RA, RB, RC: betaop(0x2A, RA, RB, RC)
XORC = lambda RA, C, RC: betaopc(0x3A, RA, C, RC)
XNOR = lambda RA, RB, RC: betaop(0x2B, RA, RB, RC)
XNORC = lambda RA, C, RC: betaopc(0x3B, RA, C, RC)
CMPEQ = lambda RA, RB, RC: betaop(0x24, RA, RB, RC)
CMPEQC = lambda RA, C, RC: betaopc(0x34, RA, C, RC)
CMPLE = lambda RA, RB, RC: betaop(0x26, RA, RB, RC)
CMPLEC = lambda RA, C, RC: betaopc(0x36, RA, C, RC)
CMPLT = lambda RA, RB, RC: betaop(0x25, RA, RB, RC)
CMPLTC = lambda RA, C, RC: betaopc(0x35, RA, C, RC)

RAND = lambda RA: betaop(0x03, RA, 0, 0)
NOP = lambda: betaop(0x02, 0, 0, 0)

BETABR = lambda OP, RA, RC, LABEL: betaopc(OP, RA, ((LABEL - dot) >> 2) - 1, RC)

BEQ = lambda RA, LABEL, RC=31: BETABR(0x1D, RA, RC, LABEL)
BF = lambda RA, LABEL, RC=31: BEQ(RA, LABEL, RC)
BNE = lambda RA, LABEL, RC=31: BETABR(0x1E, RA, RC, LABEL)
BT = lambda RA, LABEL, RC=31: BNE(RA, LABEL, RC)
BR = lambda LABEL, RC=31: BEQ(r31, LABEL, RC)
JMP = lambda RA, RC=31: betaopc(0x1B, RA, 0, RC)
# LD = lambda RA=31, CC=0, RC=31: betaopc(
#     0x18, RA, CC, RC
# )  # Janky default args since Python doesn't allow non-default args after a default arg
# ST = lambda RC, CC, RA=31: betaopc(0x19, RA, CC, RC)


def LD(RA=31, CC=0, RC=31):
    # Have to call twice because the Alchitry AU memory takes 2 clock cycles to store and load
    return betaopc(0x18, RA, CC, RC) * 2


def ST(RC, CC, RA=31):
    # Have to call twice because the Alchitry AU memory takes 2 clock cycles to store and load
    return betaopc(0x19, RA, CC, RC) * 2


LDR = lambda CC, RC: BETABR(0x1F, R31, RC, CC)
MOVE = lambda RA, RC: ADD(RA, R31, RC)
CMOVE = lambda CC, RC: ADDC(R31, CC, RC)


def PUSH(RA):
    return [ADDC(SP, 4, SP), ST(RA, -4, SP)]


def POP(RA):
    return [LD(SP, -4, RA), ADDC(SP, -4, SP)]


RTN = lambda: JMP(LP)
XRTN = lambda: JMP(XP)


# Controversial Extras
# Calling convention:
#       PUSH(argn-1)
#       ...
#       PUSH(arg0)
#       CALL(subr, nargs)
#       (return here with result in R0, args cleaned)

# Extra register conventions, for procedure linkage:
# LP = 28                       # Linkage register (holds return adr)
# BP = 29                       # Frame pointer (points to base of frame)

# Conventional stack frames look like:
#       arg[N-1]
#       ...
#       arg[0]
#       <saved lp>
#       <saved bp>
#       <other saved regs>
#   BP-><locals>
#       ...
#   SP->(first unused location)

# Convention: define a symbol for each arg/local giving bp-relative offset.
# Then use
#   getframe(name, r) gets value at offset into register r.
#   putframe(r, name) puts value from r into frame at offset name

GETFRAME = lambda OFFSET, REG: LD(bp, OFFSET, REG)
PUTFRAME = lambda REG, OFFSET: ST(REG, OFFSET, bp)


def CALL(label, N=0):
    return [BR(label, lp), SUBC(sp, 4 * N, sp)]


ALLOCATE = lambda N: ADDC(sp, N * 4, sp)
DEALLOCATE = lambda N: SUBC(sp, N * 4, sp)

# --------------------------------------------------------
# Privileged mode instructions
# --------------------------------------------------------

PRIV_OP = lambda FNCODE: betaopc(0x00, 0, FNCODE, 0)
HALT = lambda: PRIV_OP(0)
RDCHAR = lambda: PRIV_OP(1)
WRCHAR = lambda: PRIV_OP(2)
CYCLE = lambda: PRIV_OP(3)
TIME = lambda: PRIV_OP(4)
CLICK = lambda: PRIV_OP(5)
RANDOM = lambda: PRIV_OP(6)
SEED = lambda: PRIV_OP(7)
SERVER = lambda: PRIV_OP(8)

# SVC calls; used for OS extensions
# OPCODE for SVC is 0x01
SVC = lambda code: betaopc(0x01, 0, code, 0)

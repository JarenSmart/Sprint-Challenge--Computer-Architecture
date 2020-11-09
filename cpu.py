import sys
import os.path

HLT = 0b00000001
LDI = 0b10000010
PRN = 0b01000111
MUL = 0b10100010
PUSH = 0b01000101
POP = 0b01000110
CALL = 0b01010000
RET = 0b00010001
ADD = 0b10100000
CMP = 0b10100111
JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # 256-byte RAM - can store up to 255
        self.ram = [0] * 256
        # R5 = interrupt mask (IM), R6 = interrupt status (IS), R7 = stack pointer (SP)
        self.reg = [0] * 8
        # Registers
        self.pc = 0  # Program Counter - address of the currently executing instruction
        self.ir = 0  # Instruction Register - contains a copy of the currently executing instruction
        self.mar = 0  # Memory Address Register - memory address we're reading or writing
        self.mdr = 0  # Memory Data Register - the value to write or the value just read
        self.fl = 0  # Flag Register - current flags status
        self.halted = False
        self.reg[7] = 0xF4  # 244 # int('F4', 16)

        # Branch Table
        self.branchtable = {}
        self.branchtable[HLT] = self.process_HLT
        self.branchtable[LDI] = self.process_LDI
        self.branchtable[PRN] = self.process_PRN
        self.branchtable[MUL] = self.process_MUL
        self.branchtable[PUSH] = self.process_PUSH
        self.branchtable[POP] = self.process_POP
        self.branchtable[CALL] = self.process_CALL
        self.branchtable[RET] = self.process_RET
        self.branchtable[ADD] = self.process_ADD
        self.branchtable[CMP] = self.process_CMP
        self.branchtable[JMP] = self.process_JMP
        self.branchtable[JEQ] = self.process_JEQ
        self.branchtable[JNE] = self.process_JNE

    # Property wrapper for SP (Stack Pointer)
        # Stack Pointer points at the value at the top of the stack, or at address F4 if the stack is empty.

    # PROPERTIES #############################

    @property
    def sp(self):
        return self.reg[7]

    @sp.setter
    def sp(self, a):
        self.reg[7] = a & 0xFF

    @property
    def op_a(self):
        return self.ram_read(self.pc + 1)

    @property
    def op_b(self):
        return self.ram_read(self.pc + 2)

    @property
    def instruction_size(self):
        return ((self.ir >> 6) & 0b11) + 1

    @property
    def instruction_sets_pc(self):
        return ((self.ir >> 4) & 0b0001) == 1

    ##########################################

    def ram_read(self, mar):
        if mar >= 0 and mar < len(self.ram):
            return self.ram[mar]
        else:
            print(
                f"Error with read from memory address: {mar}")
            return -1

    def ram_write(self, mar, mdr):
        if mar >= 0 and mar < len(self.ram):
            self.ram[mar] = mdr & 0xFF
        else:
            print(
                f"Error with read from memory address: {mar}")

    def load(self, program_file):
        """Load a program into memory."""

        address = 0

        file_path = os.path.join(os.path.dirname(__file__), program_file)
        try:
            with open(file_path) as f:
                for line in f:
                    num = line.split("#")[0].strip()  # "10000010"
                    try:
                        instruction = int(num, 2)
                        self.ram[address] = instruction
                        address += 1
                    except:
                        continue
        except:
            print(f'Could not find file named: {program_file}')
            sys.exit(1)

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""
        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        # elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """
        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')
        for i in range(8):
            print(" %02X" % self.reg[i], end='')
        print()

    def run(self):
        """Run the CPU."""
        while not self.halted:
            self.ir = self.ram_read(self.pc)
            if self.ir in self.branchtable:
                self.branchtable[self.ir]()
            else:
                print(f"Error: Could not find instruction {self.ir}.")
                sys.exit(1)

            if not self.instruction_sets_pc:
                self.pc += self.instruction_size

    def execute_instruction(self, op_a, op_b):

        if self.ir in self.branchtable:
            self.branchtable[self.ir](op_a, op_b)
        else:
            print(f"Error: Unable to locate instruction: {self.ir}")
            sys.exit(1)

    # OPS ###########################################################

    def process_HLT(self):
        self.halted = True

    def process_LDI(self):
        self.reg[self.op_a] = self.op_b

    def process_PRN(self):
        print(self.reg[self.op_a])

    def process_MUL(self):
        self.reg[self.op_a] *= self.reg[self.op_b]

    def process_PUSH(self):
        self.sp -= 1
        self.mdr = self.reg[self.op_a]
        self.ram_write(self.sp, self.mdr)

    def process_POP(self):
        self.mdr = self.ram_read(self.sp)
        self.reg[self.op_a] = self.mdr
        self.sp += 1

    def process_CALL(self):
        self.sp -= 1
        self.ram_write(self.sp, self.pc + self.instruction_size)
        self.pc = self.reg[self.op_a]

    def process_RET(self):
        self.pc = self.ram_read(self.sp)
        self.sp += 1

    def process_ADD(self):
        self.reg[self.op_a] += self.reg[self.op_b]

    def process_CMP(self):
        if self.reg[self.op_a] < self.reg[self.op_b]:
            self.fl = 0b00000100
        elif self.reg[self.op_a] > self.reg[self.op_b]:
            self.fl = 0b00000010
        else:
            self.fl = 0b00000001

    def process_JMP(self):
        self.pc = self.reg[self.op_a]

    def process_JEQ(self):
        if self.fl == 0b00000001:
            self.process_JMP()
        else:
            self.pc += self.instruction_size

    def process_JNE(self):
        if self.fl != 0b00000001:
            self.process_JMP()
        else:
            self.pc += self.instruction_size

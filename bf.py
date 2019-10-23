"""
    bf.py
    Notes:
    Each cell holds arbitrary length signed integer because of language
    specification.
    There is no way to delete a memory of a cell to save memory once it is
    initialized.
    Logic_God please help with my memory usage from Python. If there is
    one way to optimize memory usage and performance overhead from coding
    in Python, please tell me.
    
"""
import time
import logging
from collections import deque
import sys
from typing import *


def bf_init(bf):
    # 32 cells of 0 to start with
    bf.allocated = 1
    bf.cells = [0] * 32
    bf.cell_ptr = 0
    bf.stdout = ""
    bf.stack = deque()
    bf.steps = 0

class Brainfork:
    def __init__(self, dict_, conversion_func_ptr,
                 left_right_bracket:tuple, init_ptr = bf_init):
        self.dict_char_func_ptr = dict_
        self.dict_func_char = dict((v,k) for k,v in dict_.items())
        self.symbol_conversion_ptr = conversion_func_ptr
        self.init_ptr = init_ptr
        self.l_r_tuple = left_right_bracket
    def _clean(self, symbol_collection):
        cleaned = list(filter(lambda char:char in self.dict_char_func_ptr,
                              symbol_collection))
        return cleaned
    def _get_plus(self):
        return self.dict_func_char[bf_increment]
    def _get_minus(self):
        return self.dict_func_char[bf_decrement]
    
    def _clean_op(self, symbol_collection):
        cleaned = list()
        pos = 0
        add_num = 0
        adding_sequence_triggered = False
        while pos < len(symbol_collection):
            if symbol_collection[pos] not in self.dict_char_func_ptr:
                pos += 1
                continue
            while pos < len(symbol_collection):
                if symbol_collection[pos] == self.dict_func_char[bf_increment]:
                    add_num += 1
                elif symbol_collection[pos]==self.dict_func_char[bf_decrement]:
                    add_num -= 1
                else:
                    break
                adding_sequence_triggered = True
                pos += 1
            if adding_sequence_triggered:
                if add_num == 0:
                    continue
                if add_num > 0:
                    cleaned.append(self._get_plus())
                else:
                    cleaned.append(self._get_minus())
                cleaned.append(chr(abs(add_num)))
                add_num = 0
                adding_sequence_triggered = False
                continue
            cleaned.append(symbol_collection[pos])
            pos += 1
        return cleaned
    def peek_program(self):
        cell_str = "cell:["
        for i in range(self.allocated):
            elem_str=f"{self.cells[i]}"
            if i == self.cell_ptr:
                elem_str = "<<{}>>".format(elem_str)
            cell_str+="{}, ".format(elem_str)
        if len(self.cells) > self.allocated:
            back_str = f"...({len(self.cells)-self.allocated} more allocated)]"
        else:
            back_str = "] len = {}".format(len(self.cells))
        cell_str+= back_str
        std_out = "stdout: \"{}\"".format(self.stdout)
        return "{}\n{}".format(cell_str, std_out)
    def peek_details(self):
        cell_str = "cell:["
        for i in range(len(self.cells)):
            elem_str=f"{self.cells[i]}\"{chr(self.cells[i])}\""
            if i == self.cell_ptr:
                elem_str = "<<{}>>".format(elem_str)
            cell_str+="{}, ".format(elem_str)
        cell_str+="...]"
        std_out = "stdout: \"{}\"".format(self.stdout)
        steps = "steps: {}".format(self.steps)
        return "{}\n{}\n{}".format(cell_str, std_out, steps)
    def compare(self, raw_str):
        print("==========EXECUTE============")
        self.execute(raw_str,False, True)
        print("=========EXECUTE_OP==========")
        self.execute_op(raw_str, False, True)
        
    def execute(self, raw_string, trace = False, print_immediately = False):
        start = time.time()        
        functional_symbols = self._clean(self.symbol_conversion_ptr(
            raw_string))
        self.init_ptr(self)
        code_position = [0]
        while code_position[0] < len(functional_symbols):
            exception_msg=(self.dict_char_func_ptr[
                functional_symbols[code_position[0]]](
                    self, code_position, functional_symbols, print_immediately))
            if exception_msg is not None:
                logging.error(exception_msg)
                print(self.peek_details())
                print("Code position: {}".format(code_position[0]))
                break
            if trace:
                print(self.peek_program())
            self.steps += 1
        end = time.time()
        print("============== INFO ===============")
        # print(self.stdout)
        print("clean: {}".format(' '.join(functional_symbols)))
        print(self.peek_details())
        print("Active commands: {}".format(len(functional_symbols)))
        print("Word count: {}".format(len(self.stdout)))
        print("Cells allocated: {}".format(self.allocated))
        print("Time took: {} secs".format(end-start))
        print("============= END INFO =============")
        return self.stdout
    def execute_op(self, raw_string, trace = False, print_imm = False):
        """
            A more optimized execution by grouping many commands into
            an iterative and modern-hardware-friendly one
            Ex: ++++++++++++++++ -> +"\x16"
            Ex: +- -> ''
            
        """
        start = time.time()
        # Clean the code and optimize it out
        functional_symbols = self._clean_op(self.symbol_conversion_ptr(
            raw_string))
        # Remap functions
        add_chr = self._get_plus()
        minus_chr = self._get_minus()
        self.op_dict = dict(self.dict_char_func_ptr)
        self.op_dict[add_chr] = bf_inc_op
        self.op_dict[minus_chr] = bf_dec_op        
        
        self.init_ptr(self)
        code_position = [0]
        while code_position[0] < len(functional_symbols):
            # Execute the command, store the exception message
            exception_msg=(self.op_dict[
                functional_symbols[code_position[0]]](
                    self, code_position, functional_symbols, print_imm))
            
            # There is an error in the code.
            if exception_msg is not None:
                logging.error(exception_msg)
                print(self.peek_details())
                print("Code position: {}".format(code_position[0]))
                break
            if trace:
                print(self.peek_program())
            self.steps += 1
        end = time.time()
        print("============== INFO ===============")
        # print(self.stdout)
        print("clean: {}".format(' '.join(functional_symbols)))
        print(self.peek_details())
        print("Active commands: {}".format(len(functional_symbols)))
        print("Word count: {}".format(len(self.stdout)))
        print("Cells allocated: {}".format(self.allocated))
        print("Time took: {} secs".format(end-start))
        print("============= END INFO =============")
        return self.stdout

# Brainfuck basic functions: ==================================================

def bf_right_ptr_shift(bf:Brainfork, code_position:List[int],
                       *useless_args):
    # Shift it to the right 
    bf.cell_ptr += 1
    if bf.cell_ptr >= bf.allocated:
        bf.allocated += 1
        if bf.cell_ptr >= len(bf.cells):
            # append a new int into the active cells
            bf.cells.append(0)
    code_position[0] += 1
    return None

def bf_left_ptr_shift(bf:Brainfork, code_position:List[int],
                      *useless_args):
    bf.cell_ptr -= 1
    if bf.cell_ptr < 0:
        return "Attempting to access negative-indexed cell. Undefined behavior."
    code_position[0] += 1
    return None

def bf_increment_uni(bf:Brainfork, code_position:List[int], functional_symbols,
                 *u):
    bf.cells[bf.cell_ptr] += 1
    code_position[0] += 1
    return None

def bf_decrement_uni(bf:Brainfork, code_position:List[int], functional_symbols,
                 *u):
    bf.cells[bf.cell_ptr] -= 1
    code_position[0] += 1
    return None

def bf_increment(bf:Brainfork, code_position:List[int], functional_symbols,
                 *u):
    bf.cells[bf.cell_ptr] += 1
    if bf.cells[bf.cell_ptr] == 256:
        bf.cells[bf.cell_ptr] = 0
    code_position[0] += 1
    return None

def bf_inc_op(bf: Brainfork, code_position:List[int], optimized_symbols, *u):
    operand = ord(optimized_symbols[code_position[0]+1])
    bf.cells[bf.cell_ptr] += operand
    bf.cells[bf.cell_ptr] %= 256
    code_position[0] += 2
    return None

def bf_dec_op(bf: Brainfork, code_position:List[int], optimized_symbols, *u):
    operand = (ord(optimized_symbols[code_position[0]+1])) % 256
    bf.cells[bf.cell_ptr] -= operand
    if bf.cells[bf.cell_ptr] < 0:
        bf.cells[bf.cell_ptr] += 256
    code_position[0] += 2
    return None

def bf_decrement(bf:Brainfork, code_position:List[int], functional_symbols,
                 *u):
    bf.cells[bf.cell_ptr] -= 1
    if bf.cells[bf.cell_ptr] == -1:
        bf.cells[bf.cell_ptr] = 255
    code_position[0] += 1
    return None

def bf_input(bf:Brainfork, code_position:List[int], functional_symbols,
             *u):
    """
        if inp contains more than 1 character, copy the first char value
    """
    inp = input("Requesting input (1 char only): ")
    if len(inp) > 1:
        inp = inp[0]
    bf.cells[bf.cell_ptr] = ord(inp)
    code_position[0] += 1
    return None

def bf_output(bf:Brainfork, code_position:List[int], functional_symbols,
              trace, *u):
    val = bf.cells[bf.cell_ptr]
    c = chr(val)
    bf.stdout += c
    if trace:
        sys.stdout.write(c)
    code_position[0] += 1
    return None

def bf_left_bracket(bf:Brainfork, code_position:List[int], functional_symbols,
                    *u):
    if bf.cells[bf.cell_ptr] == 0:
        # jump
        left_brackets_saw = 0
        code_position[0] += 1
        # find right bracket
        while code_position[0] < len(functional_symbols):
            if functional_symbols[code_position[0]] == bf.l_r_tuple[0]:
                left_brackets_saw += 1
            elif functional_symbols[code_position[0]] == bf.l_r_tuple[1]:
                if left_brackets_saw == 0:
                    break
                left_brackets_saw -= 1
                pass
            code_position[0] += 1
        if left_brackets_saw > 0:
            # Not matching brackets
            return "Non-matching brackets! Right not found"
    else:
        bf.stack.append(code_position[0])
    code_position[0] += 1

def bf_right_bracket(bf:Brainfork, code_position:List[int], functional_symbols,
                     *u):
    if bf.cells[bf.cell_ptr] != 0:
        try:
            jump_pos = bf.stack.pop()
            bf.stack.append(jump_pos)
        except IndexError:
            return "Non-matching brackets! Left not found"
        code_position[0] = jump_pos
        pass
    else:
        try:
            jump_pos = bf.stack.pop()
        except IndexError:
            return "Non-matching brackets! Left not found"
    code_position[0] += 1
        
# BRAINFUCK_CLASSIC ============================================================
BRAINFUCK_CLASSIC_DICT = {
    '>':bf_right_ptr_shift,
    '<':bf_left_ptr_shift,
    '+':bf_increment,
    '-':bf_decrement,
    '.':bf_output,
    ',':bf_input,
    '[':bf_left_bracket,
    ']':bf_right_bracket
    }

def brainfuck_string2syms(raw_string):
    return list(raw_string)  # Since brainfuck is operated on single characters

def brainfuck_equivalent(str_str_dict):
    for key, val in str_str_dict.items():
        str_str_dict[key] = BRAINFUCK_CLASSIC_DICT[val]
    return str_str_dict



REVERSEFUCK_DICT = {
    '>':'<',
    '<':'>',
    '+':'-',
    '-':'+',
    '.':',',
    ',':'.',
    '[':']',
    ']':'['
    }
brainfuck_equivalent(REVERSEFUCK_DICT)

def pika_string2syms(str_):
    return str_.split()
PIKALANG_DICT = {
    "pi":'+',
    "ka":'-',
    "pipi":'>',
    "pichu":'<',
    "pika":'[',
    "chu":']',
    "pikachu":'.',
    "pikapi":','
    }
brainfuck_equivalent(PIKALANG_DICT)

# ================ IMPLEMENT BRAINFUCKS HERE =======================
Brainfuck = Brainfork(BRAINFUCK_CLASSIC_DICT, brainfuck_string2syms, ('[',']'))
Reversefuck = Brainfork(REVERSEFUCK_DICT, brainfuck_string2syms,(']','['))
Pikalang = Brainfork(PIKALANG_DICT, pika_string2syms, ("pika", "chu"))

# ============== TESTING ZONE ===========================
from lite_unit_test import is_debug
if is_debug(__name__):
    from lite_unit_test import *
    use_multithreading()
    brainfk_tests = {
        # TEST 1===================================================
        ("""++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.
>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.""",):
        "Hello World!\n",
        # TEST 2===================================================
        ("""[ This program prints "Hello World!" and a newline to the screen, its
  length is 106 active command characters. [It is not the shortest.]

  This loop is an "initial comment loop", a simple way of adding a comment
  to a BF program such that you don't have to worry about any command
  characters. Any ".", ",", "+", "-", "<" and ">" characters are simply
  ignored, the "[" and "]" characters just have to be balanced. This
  loop and the commands it contains are ignored because the current cell
  defaults to a value of 0; the 0 value causes this loop to be skipped.
]
++++++++               Set Cell #0 to 8
[
    >++++               Add 4 to Cell #1; this will always set Cell #1 to 4
    [                   as the cell will be cleared by the loop
        >++             Add 2 to Cell #2
        >+++            Add 3 to Cell #3
        >+++            Add 3 to Cell #4
        >+              Add 1 to Cell #5
        <<<<-           Decrement the loop counter in Cell #1
    ]                   Loop till Cell #1 is zero; number of iterations is 4
    >+                  Add 1 to Cell #2
    >+                  Add 1 to Cell #3
    >-                  Subtract 1 from Cell #4
    >>+                 Add 1 to Cell #6
    [<]                 Move back to the first zero cell you find; this will
                        be Cell #1 which was cleared by the previous loop
    <-                  Decrement the loop Counter in Cell #0
]                       Loop till Cell #0 is zero; number of iterations is 8

The result of this is:
Cell No :   0   1   2   3   4   5   6
Contents:   0   0  72 104  88  32   8
Pointer :   ^

>>.                     Cell #2 has value 72 which is 'H'
>---.                   Subtract 3 from Cell #3 to get 101 which is 'e'
+++++++..+++.           Likewise for 'llo' from Cell #3
>>.                     Cell #5 is 32 for the space
<-.                     Subtract 1 from Cell #4 for 87 to give a 'W'
<.                      Cell #3 was set to 'o' from the end of 'Hello'
+++.------.--------.    Cell #3 for 'rl' and 'd'
>>+.                    Add 1 to Cell #5 gives us an exclamation point
>++.                    And finally a newline from Cell #6
""",):
        "Hello World!\n"
        }
    UTEST_INSTANCE.add_tests(*TestEntry.multi_init(Brainfuck.execute,
                                                   str_eq, brainfk_tests))
    reversefuck_test = {
        ("""----------]<-<---<-------<---------->>>>+
[<<<<,>+++,<-----------,+++++++++++,-,>>--,<---------------,<,-----------------,
+++++++++++++++++,-------------,-,++++++++++++++,>++++++++++++,
<----------------,++++++++++++++++++,--------,""",):
        "dCode ReverseFuck",
        ("""----------]<-<---<-------<---------->>>>+[<<<--,<-,-------,,---,>>--
,<---------------,<,---,++++++,++++++++,>>-,>----------,""",):
        "Hello World!"
        }
    UTEST_INSTANCE.add_tests(*TestEntry.multi_init(Reversefuck.execute,
                                                   str_eq, reversefuck_test))
    pika_tests = {
        ("""pi pi pi pi pi pi pi pi pi pi pika
pipi pi pipi pi pi pi pipi pi pi pi pi pi pi pi
pipi pi pi pi pi pi pi pi pi pi pi pichu pichu pichu
pichu ka chu pipi pipi pipi pi pi pi pi pi pi pi pi
pi pi pikachu pipi pi pi pi pi pi pi pi pi pi pi pi
pikachu ka ka ka ka pikachu
ka ka ka ka ka ka pikachu pi pi pi pi pi pi pi pi
pikachu pi pi pikachu ka pikachu
""",): "Pokemon"
        }
    UTEST_INSTANCE.add_tests(*TestEntry.multi_init(Pikalang.execute,
                                                   str_eq, pika_tests))
    UTEST_INSTANCE.execute()

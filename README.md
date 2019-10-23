# Python-Br-fuck-Interpreter
Many people have different methods of learning a new language. I write a Brainfuck Interpreter in the language I want to learn.

Entry program: brainfork.py
Usage: Launch with IDLE (untested for other IDEs), then use [Brainfuck, Reversefuck, or Pikalang].execute(program_string_input)
to execute the code.

You can add more Brainfuck-derived languages by creating a dict_ that maps with the symbols of Brainfuck, use brainfuck_equivalent(dict_)
to transform that dict_ to symbol-to-function pointer dict, then write function raw_2_syms that takes in a raw string and output a list of
symbols available in the dict_. Use Brainfork constructor with dict_, raw_2_syms, tuple of opening and closing bracket symbols to create
a new instance of Brainfuck-derived interpreter.

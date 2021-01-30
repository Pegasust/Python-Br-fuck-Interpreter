### Python-Br-fuck-Interpreter

# Motivation

Many people have different methods of learning a new language. I write a Brainfuck Interpreter in the language I want to learn.

# Programming features

- Basic data structures: 
dictionary
stack (dynamically manage closing, opening brackets)
function pointers (allow type meta-programming through console)

- Meta-programming: users may create an instance of brainfuck-derived languages (symbol redefinition)

- Type markers (typing module)

- Optimize code: User may use `interpreter.execute_op(...)` to execute with code optimization. 


# Entry program: brainfork.py

- Usage: Launch with IDLE (untested for other IDEs), then use [Brainfuck, Reversefuck, or Pikalang].execute(program_string_input)
to execute the code.

You can add more Brainfuck-derived languages by creating a `dict_` that maps with the symbols of Brainfuck, then use `brainfuck_equivalent(dict_)`
to transform that dict_ to symbol-to-function pointer dict.

One can then write function raw_2_syms that takes in a raw string and output a list of
symbols available in the dict_. 

Invoke Brainfork constructor with dict_, raw_2_syms, tuple of opening and closing bracket symbols to create
a new instance of Brainfuck-derived interpreter.

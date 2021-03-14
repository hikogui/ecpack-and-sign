

def get_expression(text, begin, separator):
    """Find the end of a expression or statement

    @return (index beyond the terminator, the expression, The terminator or empty on end-of-text)
    """
    end_chars = separator + "\n\r\f"
    bracket_stack = 0
    in_string = None

    end = len(text)
    i = begin
    while i < end:
        c = text[i]
        if in_string:
            if c == in_string:
                in_string = None
            elif c == "\\":
                i += 1
        elif c in "'\"":
            in_string = c
        elif c in "[({":
            bracket_stack += 1
        elif c in "])}":
            bracket_stack -= 1
        elif c in end_chars and not bracket_stack:
            break

        i += 1

    expression = text[begin:i].strip()
    terminator = text[i:i + 1]
    return i + 1, expression, terminator

def I(indent):
    return "    " * indent

def append_text(program, indent, text, i, j):
    for line in text[i:j].splitlines(True):
        program.append(I(indent) + '__r.append({})'.format(repr(line)))
    return j

def find(text, separator, i):
    j = text.find(separator, i)
    return j if j != -1 else len(text)

def parse_psp(text, separator):
    """Parse PSP text and return a python script

    @param text The text to parse.
    @param separator The separator to use to detect Python statements and expressions
    @param tab_size The size of tabs
    @param strip_count The size of initial whitespace to remove from each line.
    """
    program = ['__r = []']
    indent = 0
    i = 0

    while True:
        j = find(text, separator, i)
        i = append_text(program, indent, text, i, j)
        if i == len(text):
            break

        i, expression, terminator = get_expression(text, i + 1, separator)

        if terminator == separator and expression == "":
            # Separator escape, print the whole string.
            program.append(I(indent) + '__r.append({})'.format(repr(separator)))

        elif terminator == separator:
            # Print the result of the expression.
            program.append(I(indent) + "__r.append(str({}))".format(expression))

        elif expression.startswith("end"):
            # End a block.
            indent -= 1

        elif expression.startswith("elif ") or expression.startswith("else:"):
            # elif and else statements both end and start a block.
            program.append(I(indent - 1) + expression)

        elif expression.endswith(":"):
            # statements ending with : start a new block.
            program.append(I(indent) + expression)
            indent += 1

        else:
            # Other statement are in the current block.
            program.append(I(indent) + expression)
    
    if indent != 0:
        raise RuntimeError("Python blocks incorrectly terminated")

    return "\n".join(program)

def psp(text, namespace, separator="%"):
    """A very simple template language parser and evaluate.

    The language consists of the following elements:

    Python statement
    ----------------
    A line with a single separator '%' starts a python statement.
    The end of the Python statement is detected by a simple
    matching bracket-pair/string scanner until the end of line.

    End of block
    ------------
    A line with a single separator '%' followed by the word 'end' will end
    the current block.

    Python expression
    ------------------
    When a separator '%' is found not at the start of line the following is
    a Python expression. The end of the Python expression is detected by a simple
    matching bracket-pair/string scanner until a delimiting '%'. The result
    of the expression is converted to a string and inserted in the text.

    Separator escape
    ----------------
    A separator '%' can be escaped by doubling.

    @param text The text to parse and execute
    @param namespace A dictionary passed when evaluating the template
    @param separator The separator to use to detect python code.
    @return The result of the evaluated text.
    """

    python_code = parse_psp(text, separator)
    exec(python_code, globals(), namespace)
    return "".join(namespace["__r"])

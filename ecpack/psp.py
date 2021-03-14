

def find_end_of_expression(text, i, separator):
    """Find the end of a expression or statement

    @return index at end of expression, the matching separator, end-of-line or end-of-text
    """
    end_chars = separator + "\n\r\f"
    stack = []
    in_string = None

    end = len(text)
    while i < end:
        c = text[i]
        if c == "[":
            stack.append("]")
        elif c == "(":
            stack.append("(")
        elif c == "{":
            stack.append("{")
        elif c in "])}":
            if stack[-1] != stack.pop():
                raise RuntimeError("Found non-matching '{}'".format(c))
        elif in_string:
            if c == in_string:
                in_string = None
            elif c == "\\":
                i += 1
        elif c in "'\"":
            in_string = c

        elif c in end_chars and len(stack) == 0:
            return i

        i += 1
    else:
        return i

def escape_dqstring(text):
    """Escape all dquote and all backslashes
    """
    r = []

    for c in text:
        if c == '\\':
            r.append('\\\\')
        elif c == '"':
            r.append('\\"')
        elif c == '\n':
            r.append('\\n')
        elif c == '\r':
            r.append('\\r')
        else:
            r.append(c)

    return "".join(r)

def I(indent):
    return "    " * indent

def parse_psp(text, separator):
    """Parse PSP text and return a python script

    @param text The text to parse.
    @param separator The separator to use to detect Python statements and expressions
    @param tab_size The size of tabs
    @param strip_count The size of initial whitespace to remove from each line.
    """

    lines = ['__r = []']
    indent = 0
    str_begin = 0
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\n":
            # End of line, print the whole string, including line-feed.
            lines.append(I(indent) + '__r.append("{}\\n")'.format(escape_dqstring(text[str_begin:i])))

            # Continue past the line-feed.
            i += 1
            str_begin = i

        elif c == separator:
            lines.append(I(indent) + '__r.append("{}")'.format(escape_dqstring(text[str_begin:i])))

            j = find_end_of_expression(text, i + 1, separator)
            expression = text[i + 1:j].strip()
            terminator = text[j:j + 1]

            if terminator == separator and expression == "":
                # Separator escape, print the whole string.
                lines.append(I(indent) + '__r.append("{}")'.format(escape_dqstring(separator)))

            elif terminator == separator:
                # Print the result of the expression.
                lines.append(I(indent) + "__r.append(str({}))".format(expression))

            elif expression.startswith("end"):
                # End a block.
                indent -= 1

            elif expression.startswith("elif ") or expression.startswith("else:"):
                # elif and else statements both end the block.
                lines.append(I(indent - 1) + expression)

            elif expression.endswith(":"):
                # statements ending with : start a new block.
                lines.append(I(indent) + expression)
                indent += 1

            else:
                # Other statement are in the current block.
                lines.append(I(indent) + expression)
            
            # Jump over the expression and the terminator. 
            i = j + 1
            str_begin = i

        else:
            # Other characters are skipped.
            next_lf = text.find("\n", i)
            if next_lf == -1:
                next_lf = len(text)

            next_sep = text.find(separator, i)
            if next_sep == -1:
                next_sep = len(text)

            i = min(next_lf, next_sep)

    # print the rest
    if str_begin < len(text):
        lines.append(I(indent) + '__r.append("{}")'.format(escape_dqstring(text[str_begin:])))

    if indent != 0:
        raise RuntimeError("Python blocks incorrectly terminated")

    return "\n".join(lines)

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

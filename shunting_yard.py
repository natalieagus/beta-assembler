import re

import beta_32 as beta
from helper_functions import flip, is_number

binary_ops = ["-", "&", "|", "+", "*", "/", "%", "&", ">>", "<<"]
unary_ops = {"-": "-u", "~": "~"}

default_mapper = {"-u": lambda x: -x, "~": lambda x: str(flip(int(x)))}


def is_name(str):
    """
    Convenience function to check if a string is a valid name
    """
    return re.match("\w+", str)


def peek(stack):
    """
    Convenience function to return the top of the
    stack without removing it from the stack
    """
    return stack[-1] if stack else None


def apply_operator(operator, values):
    """
    Remove the top 2 elements of the values stack
    and the top element of the operator stack
    and apply the operator to the two values in the order
    they were added to the stack
    """
    right = values.pop()
    left = values.pop()
    values.append(str(eval(f"{left} {operator} {right}")))


def apply_function(func, values):
    """
    Remove elements from the values stack until we meet the wall character '@'
    then call the function specified on the values removed
    """
    args = []
    while (top := values.pop()) != "@":
        args.insert(0, int(top))

    # Keep args in the correct position
    values.append(str(func(*args)))


def greater_precedence(op1, op2):
    """
    Returns a boolean indicating if op1 has greater precedence than op2
    """
    precedences = {
        "+": 0,
        "-": 0,
        "&": 1,
        "|": 1,
        ">>": 2,
        "<<": 2,
        "*": 3,
        "/": 3,
        "%": 3,
        "-u": 4,
        "~u": 4,
    }
    return precedences[op1] > precedences[op2]


def convert(expression, dot, labels):
    """
    Convert the given expression to postfix notation,
    substituting '.' and any labels as necessary
    """
    sub_pattern = re.compile("([+\/*()\-%])")
    search_pattern = re.compile("[+\/*()\-%]|>>|<<|[\d\w.]+")
    tokens = search_pattern.findall(sub_pattern.sub(r" \1 ", expression))
    prev_op = True
    output = []
    operators = []
    for token in tokens:
        if num := is_number(token):
            output.append(str(num[0]))
            prev_op = False
        elif hasattr(beta, token):
            output.append(token)
            prev_op = False
        elif token in labels:
            output.append(labels[token])
            prev_op = False
        elif token == ".":
            # Current address
            output.append(dot)
            prev_op = False
        elif token == "(":
            operators.append(token)
            prev_op = True
        elif token == ")":
            top = peek(operators)
            while top != "(":
                if top is None:
                    raise Exception("Invalid expression")
                output.append(operators.pop())
                top = peek(operators)
            if peek(operators) != "(":
                raise Exception("Mismatching parenthesis")
            operators.pop()  # Discard the '('

            if (
                (top := peek(operators)) is not None
                and top not in binary_ops
                and top not in "()"
            ):
                # Function
                output.append(operators.pop())
        else:
            # Operator
            if token not in binary_ops:
                # Function
                operators.append(token)

                # Append a wall token to know the end of variable length function arguments
                output.append("@")
            else:
                if prev_op:
                    # Unary operator
                    # Treat it like a function
                    # Put in separate branch so that we can replace the symbol as appropriate with an unary symbol
                    operators.append(unary_ops[token])
                    output.append("@")

                else:
                    # Binary operator
                    top = peek(operators)
                    while (
                        top is not None
                        and top not in "()"
                        and greater_precedence(top, token)
                    ):
                        output.append(operators.pop())
                        top = peek(operators)

                    operators.append(token)

                    prev_op = True

    while peek(operators) is not None:
        if peek(operators) == "(":
            raise Exception("Mismatching parenthesis")
        output.append(operators.pop())

    return " ".join(output)


def substitute(macro_args, definition_args, postfix_expr):
    """
    Takes the macro_args of the caller, the definition_args of the called function, and the postfix_expr of the called function,
    and substitutes in the caller's args and returns it
    """
    try:
        assert len(macro_args) == len(definition_args)

        # Assume positionality of arguments
        for idx, arg in enumerate(definition_args):
            for jdx, expr in enumerate(postfix_expr):
                postfix_expr[jdx] = (
                    2,
                    re.sub(f"(^| ?){arg} ", f" {macro_args[idx]} ", expr[1]),
                )
        return postfix_expr
    except Exception as e:
        print(e)
        print(macro_args)
        print(definition_args)
        print(postfix_expr)
        exit()


def evaluate(expression, dot, labels):
    """
    Takes the expression and evaluates it
    """
    postfix_expr = convert(expression, dot, labels)
    split_pattern = re.compile("[+\/*()\-%]|>>|<<|[\d\w.]+")

    stack = []
    for token in split_pattern.finditer(postfix_expr):
        if token.group(0).isnumeric() or token.group(0) == "@":
            stack.append(token.group(0))
        elif token.group(0) in binary_ops:
            apply_operator(token.group(0), stack)
        else:
            # Function
            apply_function(default_mapper[token.group(0)], stack)
    return stack[-1]


def main():
    expression = "SUBC(sp, N*4, sp)"
    val = convert(expression, ["N"], {"sp": "29"})
    print(f"Shunting Yard Algorithm: {val}")
    # print(f"Eval: {evaluate(val, {})}")

    print(substitute(["RA"], ["x"], [(2, "x 256 %"), (2, "x 8 >> 256 %")]))


if __name__ == "__main__":
    main()

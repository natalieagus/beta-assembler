import pathlib
import re
import sys 
import traceback

import beta_32 as beta
import shunting_yard
from helper_functions import is_number

comment_pattern = re.compile(r"\|.*")
label_pattern = re.compile(r"(^.*:)[ \t]*?(.+)$", re.M)
instruction_chunk_pattern = re.compile(r"\)[ \t]+?([a-zA-Z])")
whitespace_pattern = re.compile(r"^[ \t]+(.*)[ \t]*?$", re.M)
newline_pattern = re.compile(r"\n{2,}")

instruction_pattern = re.compile(r"(.*)\((.*)\)")
expression_pattern = re.compile(r"(\d|\))[ \t]+?(\(|\d)")

output_formatter = {
    "bin": (bin, 8, "b"),
    "hex": (hex, 2, "h"),
}


def write_data(x, counter, data_store):
    """
    Convenience function to write x to data_store, at position counter onwards

    If counter is greater than len(data_store), the function will append x

    If counter is less than len(data_store), the function will overwrite the data at that position
    """
    if counter == len(data_store):
        # Appending to the end
        # Memory padding is done in the second loop so we can assume that data_store is valid here (either == or <)
        data_store.extend(x)
        counter += len(x)
    else:
        for b in x:
            if counter < len(data_store):
                # Inserting in preexisting data
                data_store[counter] = b
            else:
                data_store.append(b)
            counter += 1

    return counter, data_store


def parse_asm(data_memory, existing_labels=None, output_format="bin"):
    """
    Convert the assembly in file <filename> to bytecode

    existing_labels is a dict containing label-to-address mappings
    """
    if existing_labels is None:
        existing_labels = {}

    data = []  # Store data values
    beta.dot = 0  # Number of data values(?)
    labels = {}  # Label-to-address mapping

    # ! output_func and output_size not currently being used for anything
    # ? Being used by WORD()?
    output_func, output_size, _ = output_formatter[output_format]
    beta.output_func = output_func
    beta.output_size = output_size

    # Remove anything after a '|'
    data_memory = comment_pattern.sub("", data_memory)

    # Split 'label: instruction' to:
    #     label:
    #     instruction
    data_memory = label_pattern.sub("\\1\n\\2", data_memory)

    # Split 'instruction1 instruction2 ...' to:
    #     instruction1
    #     instruction2
    #     ....
    data_memory = instruction_chunk_pattern.sub(")\n\\1", data_memory)

    # Just to be REALLY sure its clean
    for _ in range(2):
        # Remove whitespace in each row
        data_memory = whitespace_pattern.sub("\\1", data_memory)

        # Remove unnecessary newline characters
        data_memory = newline_pattern.sub("\n", data_memory)

    # Remove whitespace in each row
    data_memory = [i.strip() for i in data_memory.split("\n") if i.strip()]

    # First pass
    # Call each of our instructions with dummy values to solve for our label addresses
    for row in data_memory:
        if row:
            if row[-1] == ":":
                # Handle labels

                labels[row[:-1]] = beta.dot
            elif "=" in row:
                left, right = row.split("=")
                left = left.strip()
                right = right.strip()
                if left == ".":
                    # Changing memory address
                    if num := is_number(right):
                        # Most likely a number
                        beta.dot = num[0]
                    else:
                        # Most likely an expression
                        beta.dot = shunting_yard.evaluate(right, beta.dot, labels)

                else:
                    # Assignment statement
                    # Try evaluating
                    # If not possible, then evaluate on second pass (might depend on labels)
                    try:
                        if num := is_number(right):
                            setattr(
                                beta,
                                left,
                                int(shunting_yard.evaluate(right, beta.dot, labels)),
                            )
                        else:
                            setattr(
                                beta,
                                left,
                                shunting_yard.evaluate(right, beta.dot, labels),
                            )
                    except:
                        pass
            else:
                # Everything else
                if match := instruction_pattern.match(row):
                    # Instruction
                    name = match.group(1)

                    # If this instruction has args, set our dummy args to 0 * length of the args
                    # Else set to empty list
                    args = (
                        [0] * len(match.group(2).split(",")) if match.group(2) else []
                    )

                    if not hasattr(beta, name):
                        raise Exception(f"Instruction '{name}' is undefined.")

                    # We have verified that the instruction exists in beta.py
                    # We now get the function reference with getattr()
                    # and then we call it, passing it our arguments
                    instructions = getattr(beta, name)(*args)
                    beta.dot += len(instructions)
                else:
                    # Might be hex or binary code put into the file
                    row = expression_pattern.sub("\\1\n\\2", row)
                    result = []
                    for expression in row.split("\n"):
                        result.append(
                            output_func(
                                int(
                                    shunting_yard.evaluate(expression, beta.dot, labels)
                                )
                            )[2:].zfill(output_size)[-output_size:]
                        )
                    beta.dot, data = write_data(result, beta.dot, data)

    # Reset our parsed data memory array
    data = []
    beta.dot = 0
    # Second pass
    # Now we can properly evaluate our instructions with labels
    for row in data_memory:
        if row:
            if row[-1] == ":":
                # No longer need to be concerned with labels
                pass
            elif "=" in row:
                left, right = row.split("=")
                left = left.strip()
                right = right.strip()
                if left == ".":
                    # Changing memory address
                    if num := is_number(right):
                        right = num[0]
                    else:
                        # Most likely an expression
                        right = shunting_yard.evaluate(right, beta.dot, labels)

                    if beta.dot > right:
                        # Most likely a number
                        beta.dot = right
                    else:
                        # Pad with 0 bytes
                        data.extend(["0" * output_size] * (right - len(data)))

                        beta.dot = right
                else:
                    # Assignment statement
                    # Try evaluating one more time
                    try:
                        if num := is_number(right):
                            setattr(
                                beta,
                                left,
                                int(shunting_yard.evaluate(right, beta.dot, labels)),
                            )
                        else:
                            setattr(
                                beta,
                                left,
                                shunting_yard.evaluate(right, beta.dot, labels),
                            )
                    except Exception as ex:
                        raise Exception(f"Could not resolve expression {right}") from ex
            else:
                # Everything else
                if match := instruction_pattern.match(row):
                    # Instruction
                    name = match.group(1)

                    args = []
                    if match.group(2):
                        for arg in match.group(2).split(","):
                            arg = arg.strip()
                            if num := is_number(arg):
                                args.append(num[0])
                            elif arg in labels:
                                # Label
                                args.append(labels[arg])
                            elif arg in existing_labels:
                                args.append(existing_labels[arg])
                            elif hasattr(beta, arg):
                                # Check for symbolic names such as R31
                                args.append(getattr(beta, arg))
                            else:
                                print(match.group(2).split(","))
                                raise Exception(
                                    f"Invalid argument {arg} at instruction {match.group(0)}"
                                )
               
                    instructions = getattr(beta, name)(*args)
                    beta.dot, data = write_data(instructions, beta.dot, data)
                else:
                    # Might be hex or binary code put into the file
                    row = expression_pattern.sub("\\1\n\\2", row)
                    result = []
                    for expression in row.split("\n"):
                        result.append(
                            output_func(
                                int(shunting_yard.evaluate(row, beta.dot, labels))
                            )[2:].zfill(output_size)[-output_size:]
                        )
                    beta.dot, data = write_data(result, beta.dot, data)

    return data, labels


def parse_asm_file(
    input_filename,
    output_filename=None,
    existing_labels=None,
    input_format="data",
    output_format="bin",
):
    """
    Convenience function to parse a file and convert its contents to bytecode
    """

    print("input_filename", input_filename)
    data_file = pathlib.Path(input_filename).resolve()

    if data_file.exists():
        with open(input_filename, mode="r", encoding="utf-8") as fp:
            data_memory = fp.read()
    else:
        return None, None

    data, labels = parse_asm(data_memory, existing_labels, output_format)

    # Write to file
    with open(f"{output_filename}", "w+", encoding="utf8") as fp:
        # Write in reverse since const indexing in Lucid starts from the right
        fp.write(
            arr_to_str(data, input_format=input_format, output_format=output_format)
        )

    return data, labels


def arr_to_str(data, input_format, output_format):
    """
    Converts an array of bytes to a string
    """
    output_prefix = output_formatter[output_format][2]
    try:
        if input_format == "data":
            return "\n".join(
                [
                    f"{output_prefix}{''.join(data[i : min(i + (beta.memory_width // 8), len(data))][::-1])},"
                    for i in range(0, len(data), (beta.memory_width // 8))
                ][::-1]
            )
        else:
            return "\n".join(
                [
                    f"{output_prefix}{''.join(data[i : min(i + (beta.instruction_width // 8), len(data))][::-1])},"
                    for i in range(0, len(data), (beta.instruction_width // 8))
                ][::-1]
            )
    except Exception:
        print(traceback.format_exc())
        

if __name__ == "__main__":
    filename = sys.argv[1]
    output_filename = filename + ".hex"
    file_type = sys.argv[2]; # "instr" or "data" 
    parse_asm_file(input_filename=filename, output_filename=output_filename, existing_labels=None, input_format=file_type, output_format="hex")
    

import argparse
from assembler import parse_asm_file
import sys

if __name__ == "__main__":

        parser = argparse.ArgumentParser(
            description="Python assembler for MIT Beta ISA.",
        )
        parser.add_argument(
            "filename",
            type=str,
            help="The filename where filename.uasm and optionally filename_data.uasm are to be assembled.",
        )
        parser.add_argument(
            "-x", "--hex", action="store_true", help="Output hexadecimal"
        )
        parser.add_argument(
            "-b", "--bin", action="store_true", help="Output binary (default)"
        )
        parser.add_argument(
            "-s", "--silent", action="store_true", help="Disable printing to console"
        )
        parser.add_argument(
            "-o",
            "--out",
            metavar="filename",
            type=str,
            help="Specify name of output file (If not specified, defaults to filename)",
        )

        args = parser.parse_args(sys.argv[1:])
        print(args)
        input_filename = args.filename

        if args.bin or not (args.bin or args.hex):
            # Writing this way defaults to binary
            output_format = "bin"
        else:
            output_format = "hex"

        silent = args.silent

        if args.out is not None:
            output_filename = args.out
        else:
            output_filename = input_filename
        # try:
        #     self.file = sys.argv[1]
        # except IndexError as _:
        #     # Filename not passed
        #     self.file = None

        # if self.file is None:
        #     self.body = PanelWidget(
        #         Panel(
        #             "Please specify a [italic cyan]filename[/italic cyan], where:\n- The [magenta]instruction memory[/magenta] can be found in [italic cyan]filename.uasm[/italic cyan],\n- The [yellow]optional[/yellow] [magenta]data memory[/magenta] can be found in [italic cyan]filename_data.uasm[/italic cyan].",
        #             title="[bold red]Error:[/bold red] No file specified.",
        #         )
        #     )

        data_mem, data_labels = parse_asm_file(
            input_filename=f"{input_filename}_data.uasm",
            output_filename=f"{output_filename}_data.{output_format}",
            existing_labels=None,
            input_format="data",
            output_format=output_format,
        )
        instruction_mem, instruction_labels = parse_asm_file(
            input_filename=f"{input_filename}.uasm",
            output_filename=f"{output_filename}.{output_format}",
            existing_labels=data_labels,
            input_format="instr",
            output_format=output_format,
        )
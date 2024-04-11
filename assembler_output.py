import argparse
import sys
import beta_16 as beta

import pyperclip as pc
from rich.console import RenderableType
from rich.panel import Panel
from rich.syntax import Syntax
from rich_argparse import RichHelpFormatter
from textual.app import App
from textual.widget import Widget
from textual.widgets import Footer, Header, ScrollView

from assembler import arr_to_str, parse_asm_file


class PanelWidget(Widget):
    """A widget that renders a rich panel."""

    def __init__(self, panel: Panel, **kwargs) -> None:
        self.panel = panel
        super().__init__(**kwargs)

    def render(self) -> RenderableType:
        return self.panel


class MyApp(App):
    async def on_load(self) -> None:
        """Sent before going in to application mode."""

        # Bind our basic keys
        await self.bind("q", "quit", "Quit")
        await self.bind("1", "copy_orig_data", "Copy orig data mem")
        await self.bind("2", "copy_parsed_data", "Copy parsed data mem")
        await self.bind("3", "copy_orig_instr", "Copy orig instr mem")
        await self.bind("4", "copy_parsed_instr", "Copy parsed instr mem")

        parser = argparse.ArgumentParser(
            description="Python assembler for MIT Beta ISA.",
            formatter_class=RichHelpFormatter,
        )
        parser.add_argument(
            "filename",
            type=str,
            help="The [italic cyan]filename[/italic cyan] where [italic cyan]filename.uasm[/italic cyan] and optionally [italic cyan]filename_data.uasm[/italic cyan] are to be assembled.",
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
            help="Specify name of output file (If not specified, defaults to [italic cyan]filename[/italic cyan])",
        )

        args = parser.parse_args(sys.argv[1:])
        print(args)

        self.input_filename = args.filename

        if args.bin or not (args.bin or args.hex):
            # Writing this way defaults to binary
            self.output_format = "bin"
        else:
            self.output_format = "hex"

        self.silent = args.silent

        if args.out is not None:
            self.output_filename = args.out
        else:
            self.output_filename = self.input_filename
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

        self.data_mem, self.data_labels = parse_asm_file(
            input_filename=f"{self.input_filename}_data.uasm",
            output_filename=f"{self.output_filename}_data.{self.output_format}",
            existing_labels=None,
            input_format="data",
            output_format=self.output_format,
        )
        self.instruction_mem, self.instruction_labels = parse_asm_file(
            input_filename=f"{self.input_filename}.uasm",
            output_filename=f"{self.output_filename}.{self.output_format}",
            existing_labels=self.data_labels,
            input_format="instr",
            output_format=self.output_format,
        )

        self.widgets = []

        if self.instruction_mem is None:
            self.widgets.append(
                PanelWidget(
                    Panel(
                        f"Please check that the [italic cyan]filename[/italic cyan] specified exists.\n[italic cyan]filename[/italic cyan]: {self.input_filename}",
                        title="[bold red]Error:[/bold red] File does not exist.",
                    )
                )
            )
        elif not self.silent:
            # Create our widgets
            # In this a scroll view for the code and a directory tree
            self.widgets.append(
                ScrollView(
                    Syntax.from_path(
                        f"{self.input_filename}_data.uasm",
                        "utf8",
                        "asm",
                        "monokai",
                        line_numbers=True,
                        word_wrap=True,
                    )
                )
            )
            self.widgets.append(
                ScrollView(
                    Syntax(
                        arr_to_str(self.data_mem, "data", self.output_format),
                        "asm",
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=True,
                    )
                )
            )
            self.widgets.append(
                ScrollView(
                    Syntax.from_path(
                        f"{self.input_filename}.uasm",
                        "utf8",
                        "asm",
                        "monokai",
                        line_numbers=True,
                        word_wrap=True,
                    )
                )
            )
            self.widgets.append(
                ScrollView(
                    Syntax(
                        arr_to_str(self.instruction_mem, "instr", self.output_format),
                        "asm",
                        line_numbers=True,
                        theme="monokai",
                        word_wrap=True,
                    )
                )
            )
        else:
            sys.exit()

    async def on_mount(self) -> None:
        """Call after terminal goes in to application mode"""
        # Dock our widgets
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        # Note the directory is also in a scroll view
        await self.view.dock(*self.widgets, edge="left")

    async def action_copy_orig_data(self) -> None:
        """Copy original data memory to clipboard."""
        pc.copy(open(f"{self.input_filename}_data.uasm", "r").read())

    async def action_copy_parsed_data(self) -> None:
        """Copy parsed data memory to clipboard."""
        pc.copy(arr_to_str(self.data_mem, "data", self.output_format))

    async def action_copy_orig_instr(self) -> None:
        """Copy original instruction memory to clipboard."""
        pc.copy(open(f"{self.input_filename}.uasm", "r").read())

    async def action_copy_parsed_instr(self) -> None:
        """Copy parsed instruction memory to clipboard."""
        pc.copy(arr_to_str(self.instruction_mem, "instr", self.output_format))


if __name__ == "__main__":
    # Run our app class
    MyApp.run(title="Assembler Output", log="textual.log")

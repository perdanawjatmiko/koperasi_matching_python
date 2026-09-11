import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .config import (
    DEFAULT_OUTPUT,
    DEFAULT_REFERENCE,
    DuplicatePolicy,
    MatchConfig,
    timestamped_output_path,
)
from .pipeline import run
from .workbook_reader import inspect_workbook

app = typer.Typer(
    help="Cocokkan alamat wilayah dengan data referensi koperasi.", no_args_is_help=True
)


@app.command("match")
def match_command(
    source: Annotated[Path, typer.Argument(help="Workbook sumber berisi kolom ALAMAT")],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Nama dasar output; timestamp ditambahkan otomatis",
        ),
    ] = DEFAULT_OUTPUT,
    sheets: Annotated[
        list[str] | None,
        typer.Option(
            "--sheet",
            "--sheets",
            help="Sheet sumber; default memproses semua sheet dengan kolom ALAMAT",
        ),
    ] = None,
    reference: Annotated[
        Path, typer.Option("--reference", help="Workbook referensi")
    ] = DEFAULT_REFERENCE,
    address_column: Annotated[str, typer.Option("--address-column")] = "ALAMAT",
    reference_sheet: Annotated[str, typer.Option("--reference-sheet")] = "Export Laporan",
    threshold: Annotated[float, typer.Option("--threshold")] = 90.0,
    minimum_margin: Annotated[float, typer.Option("--minimum-margin")] = 5.0,
    duplicate_policy: Annotated[
        DuplicatePolicy, typer.Option("--duplicate-policy")
    ] = DuplicatePolicy.KEEP,
    overwrite: Annotated[bool, typer.Option("--overwrite")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s: %(message)s"
    )
    try:
        timestamped_output = timestamped_output_path(output)
        config = MatchConfig(
            source=source,
            reference=reference,
            output=timestamped_output,
            sheets=sheets or [],
            address_column=address_column,
            reference_sheet=reference_sheet,
            threshold=threshold,
            minimum_margin=minimum_margin,
            duplicate_policy=duplicate_policy,
            overwrite=overwrite,
        )
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        ) as progress_ui:
            task_id = progress_ui.add_task("Menyiapkan proses", total=None)

            def update_progress(message: str, current: int, total: int) -> None:
                if total > 0:
                    progress_ui.update(
                        task_id,
                        description=message,
                        total=total,
                        completed=current,
                    )
                else:
                    progress_ui.update(
                        task_id,
                        description=message,
                        total=None,
                        completed=0,
                    )

            counts = run(config, progress=update_progress)
    except (ValueError, ValidationError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(2) from error
    typer.echo(f"Selesai: {config.output}")
    for status, count in sorted(counts.items()):
        typer.echo(f"  {status}: {count}")


@app.command("inspect")
def inspect_command(
    file: Annotated[Path, typer.Argument(help="Workbook yang akan diperiksa")],
) -> None:
    if not file.is_file() or file.suffix.lower() != ".xlsx":
        typer.echo(f"Error: file XLSX tidak ditemukan: {file}", err=True)
        raise typer.Exit(2)
    typer.echo(json.dumps(inspect_workbook(file), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()

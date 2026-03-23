"""
Sinehan RAG — interactive CLI.
Run: python cli.py

Slash commands:
  /ingest <file>       Ingest a markdown file
  /ingest <file> --doc-id <id> --url <url>
  /docs                List ingested documents
  /clear <doc_id>      Remove a document
  /help                Show this help
  /exit                Quit (also Ctrl+C)

Anything else is treated as a question.
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

HELP_TEXT = """\
[bold]Slash commands[/bold]
  [cyan]/ingest <file>[/cyan]                       Ingest a markdown file
  [cyan]/ingest <file> --doc-id <id>[/cyan]         Custom doc ID
  [cyan]/ingest <file> --url <url>[/cyan]           Source URL for citations
  [cyan]/docs[/cyan]                                List all ingested documents
  [cyan]/clear <doc_id>[/cyan]                      Remove a document from Qdrant
  [cyan]/help[/cyan]                                Show this help
  [cyan]/exit[/cyan]                                Quit

[bold]Anything else[/bold] is sent to the RAG pipeline as a question.\
"""


def cmd_ingest(args: list[str]) -> None:
    if not args:
        console.print("[red]Usage: /ingest <file> [--doc-id <id>] [--url <url>][/red]")
        return

    file = Path(args[0])
    doc_id = None
    url = ""

    i = 1
    while i < len(args):
        if args[i] == "--doc-id" and i + 1 < len(args):
            doc_id = args[i + 1]
            i += 2
        elif args[i] == "--url" and i + 1 < len(args):
            url = args[i + 1]
            i += 2
        else:
            i += 1

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        return

    doc_id = doc_id or file.stem.replace(" ", "-").lower()

    from app.services.text_cleaner import clean_text
    from app.services.chunker import chunk_markdown
    from app.services.embedder import embed_chunks
    from app.services.vector_store import (
        COLLECTION_NAME, ensure_collection, delete_by_doc_id, upsert_chunks,
    )

    console.print(f"\n[bold]Ingesting[/bold] {file.name}  →  doc_id=[cyan]{doc_id}[/cyan]")

    raw = file.read_text(encoding="utf-8")
    chunks = chunk_markdown(clean_text(raw), doc_id=doc_id, sourcename=file.name, url=url)
    console.print(f"  Chunked:  [green]{len(chunks)} chunks[/green]")

    with console.status("Embedding..."):
        vectors = embed_chunks(chunks)
    console.print(f"  Embedded: [green]{len(vectors)} vectors[/green]")

    with console.status("Storing in Qdrant..."):
        ensure_collection(COLLECTION_NAME)
        delete_by_doc_id(doc_id, COLLECTION_NAME)
        upsert_chunks(chunks, vectors, COLLECTION_NAME)

    console.print(f"[bold green]✓[/bold green] {len(chunks)} chunks ingested as [cyan]{doc_id}[/cyan]\n")


def cmd_docs() -> None:
    from app.services.vector_store import _get_client, COLLECTION_NAME

    client = _get_client()
    if not client.collection_exists(COLLECTION_NAME):
        console.print("[yellow]No collection found. Run /ingest first.[/yellow]")
        return

    seen: dict = {}
    offset = None
    with console.status("Scanning..."):
        while True:
            result, offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                offset=offset,
                with_payload=["doc_id", "source_name"],
            )
            for point in result:
                p = point.payload or {}
                did = p.get("doc_id", "unknown")
                if did not in seen:
                    seen[did] = {"source_name": p.get("source_name", ""), "chunks": 0}
                seen[did]["chunks"] += 1
            if offset is None:
                break

    if not seen:
        console.print("[yellow]No documents found.[/yellow]")
        return

    table = Table(header_style="bold")
    table.add_column("doc_id", style="cyan")
    table.add_column("source")
    table.add_column("chunks", justify="right")
    for did, info in seen.items():
        table.add_row(did, info["source_name"], str(info["chunks"]))
    console.print(table)


def cmd_clear(args: list[str]) -> None:
    if not args:
        console.print("[red]Usage: /clear <doc_id>[/red]")
        return

    doc_id = args[0]
    if not console.input(f"Delete all chunks for [cyan]{doc_id}[/cyan]? (y/N) ").strip().lower() == "y":
        console.print("[dim]Cancelled.[/dim]")
        return

    from app.services.vector_store import delete_by_doc_id, COLLECTION_NAME
    delete_by_doc_id(doc_id, COLLECTION_NAME)
    console.print(f"[green]✓[/green] Deleted [cyan]{doc_id}[/cyan]")


def ask(question: str, top_k: int = 3) -> None:
    from app.services.embedder import embed_text
    from app.services.vector_store import search
    from app.services.llm import answer_from_chunks

    with console.status("Thinking..."):
        vec = embed_text(question)
        chunks = search(vec, top_k=top_k)
        answer = answer_from_chunks(question, chunks)

    console.print(Panel(answer, title="[bold green]Answer[/bold green]", border_style="green"))

    if chunks:
        table = Table(show_header=True, header_style="bold dim", box=None, padding=(0, 2))
        table.add_column("#", style="dim", width=3)
        table.add_column("Section")
        table.add_column("doc_id", style="cyan")
        for i, c in enumerate(chunks, 1):
            table.add_row(str(i), c.get("section_title", ""), c.get("doc_id", ""))
        console.print(table)


def main() -> None:
    console.print(Panel(
        "[bold]Sinehan RAG[/bold]\n[dim]Ask a question or type [cyan]/help[/cyan] for commands.[/dim]",
        border_style="blue",
    ))

    while True:
        try:
            line = console.input("\n[bold cyan]>[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye.[/dim]")
            break

        if not line:
            continue

        if line.startswith("/"):
            parts = line[1:].split()
            cmd, args = parts[0].lower() if parts else "", parts[1:]

            if cmd in ("exit", "quit"):
                console.print("[dim]Bye.[/dim]")
                break
            elif cmd == "help":
                console.print(Panel(HELP_TEXT, border_style="dim"))
            elif cmd == "ingest":
                cmd_ingest(args)
            elif cmd == "docs":
                cmd_docs()
            elif cmd == "clear":
                cmd_clear(args)
            else:
                console.print(f"[red]Unknown command: /{cmd}[/red]  Type [cyan]/help[/cyan]")
        else:
            ask(line)


if __name__ == "__main__":
    main()

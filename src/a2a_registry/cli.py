"""Command line interface for a2a-registry."""

import click
import uvicorn


@click.group()
def cli() -> None:
    """A2A Registry CLI."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the A2A Registry JSON-RPC server."""
    click.echo(f"Starting A2A Registry server on {host}:{port}")
    uvicorn.run(
        "a2a_registry.server:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

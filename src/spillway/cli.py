import typer

app = typer.Typer()


@app.callback()
def main():
    """Spillway: AWS Security Hub to Jira Dispatcher"""
    pass


@app.command()
def triage():
    pass

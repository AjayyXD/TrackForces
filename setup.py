from database import db
import questionary
from rich.console import Console
console = Console()
def run_setup():
    database_handler = db.database_handler()
    handle = questionary.text("What is your codeforces handle?").ask()
    with console.status("[bold cyan]Querying Codeforces for data...[/bold cyan]", spinner="bouncingBar"):
        database_handler.init_fill_submission(handle)
    console.print("\n[bold green]✔ Data fetched from codeforces.[/bold green]")

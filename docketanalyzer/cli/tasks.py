import os
import click
from docketanalyzer import load_docket_index


@click.command()
@click.option('--name', '-n', default=None, help='Task to run.')
@click.option('--run', '-r', is_flag=True, help='Run the task.')
def tasks(name, run):
    """
    Run a registered task across the default docket index.
    """
    index = load_docket_index()
    for task in index.tasks.values():
        if name is None or task.name == name:
            if run:
                task.run()
                print(task.progress_str)
            else:
                print(task.name)
                print('\t', task.__doc__.strip())
                print()
    if not run:
        print('Add --run to execute the task.')

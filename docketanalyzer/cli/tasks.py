import os
import click
from docketanalyzer import load_docket_index


@click.command()
@click.option('--name', '-n', default=None, help='Task to run.')
@click.option('--run', '-r', is_flag=True, help='Run the task.')
@click.option('--reset', is_flag=True, help='Reset the task progress (only applied if a single task is selected).')
def tasks(name, run, reset):
    """
    Run a registered task across the default docket index.
    """
    index = load_docket_index()
    for task in index.ordered_tasks:
        if name is None or task.name == name:
            print(task.name)
            print(task.progress_str)
            if run:
                if name is not None and reset:
                    confirm = input(f'Are you sure you want to reset {task.name}? (y/n): ')
                    if confirm.lower() != 'y':
                        print('Task reset aborted.')
                        return
                    task.reset()
                task.run()
            else:
                print(task.__doc__.strip())
                print()
    if not run:
        print('Add --run to execute the task.')

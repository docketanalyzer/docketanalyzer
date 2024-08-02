import os
import click
from docketanalyzer import load_docket_index


@click.command()
@click.argument('name', default=None, required=False)
@click.option('--custom-only', '-c', is_flag=True, help='Only list or run custom tasks.')
@click.option('--skip', '-s', default=None, help='Comma-separated list of tasks to skip.')
@click.option('--run', '-r', is_flag=True, help='Run the task.')
@click.option('--reset', is_flag=True, help='Reset the task progress (only applied if a single task is selected).')
def tasks(name, custom_only, skip, run, reset):
    """
    List or run registered tasks across the default docket index.

    If no NAME is provided, this command lists all available tasks.
    If a NAME is provided, it either shows details about that task or runs it,
    depending on the --run flag.

    Arguments:
    NAME: The name of the task to run or get information about. Optional.

    Options:
    --custom-only, -c: If set, only list or operate on user-defined tasks, excluding built-in tasks.
    --skip, -s: Comma-separated list of tasks to skip.
    --run, -r: Run the specified task. If not set, only display task information.
    --reset: Reset the progress of the specified task. Only applies when a single task is selected.

    Built-in tasks are provided by the system, and users can register their own custom tasks.
    To register a custom task, use the register_task function:

    from docketanalyzer import Task, register_task

    class CustomTask(Task):
        # Task implementation

    register_task(CustomTask)

    Example usage:
    da tasks  # List all tasks
    da tasks mytask  # Show information about 'mytask'
    da tasks mytask --run  # Run 'mytask'
    da tasks mytask --run --reset  # Run 'mytask' after resetting its progress
    """
    index = load_docket_index()
    tasks = list(index.ordered_tasks)
    skip = [] if skip is None else skip.split(',')
    for task in tasks:
        if task.name not in skip:
            if not custom_only or task.custom:
                if name is None or task.name == name:
                    print(task.name)
                    print(task.progress_str)
                    if name is not None and reset:
                        confirm = input(f'Are you sure you want to reset {task.name}? (y/n): ')
                        if confirm.lower() != 'y':
                            print('Task reset aborted.')
                            return
                        task.reset()
                    if run:
                        task.run()
                    else:
                        print(task.__doc__.strip())
                        print()
    if not run:
        print('Add --run to execute the task.')

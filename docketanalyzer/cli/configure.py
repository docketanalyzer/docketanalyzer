import click
import docketanalyzer

config_groups_str = list(set([x.group for x in docketanalyzer.config.keys if x.group]))
config_groups_str = ', '.join(config_groups_str)

@click.command()
@click.option('--reset', is_flag=True)
@click.option('--group', '-g', default=None, type=str, help=f'Filter config keys by group, which can be one of: ({config_groups_str})')
def configure(reset, group):
    docketanalyzer.config.update(reset=reset, group=group)

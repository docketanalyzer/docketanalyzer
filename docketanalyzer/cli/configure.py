import click
import docketanalyzer


def get_config_groups():
    return list(set([x.group for x in docketanalyzer.config.keys if x.group]))


config_groups = get_config_groups()
config_groups_str = ', '.join(config_groups)


class ConfigGroup(click.ParamType):
    name = "group"

    def convert(self, value, param, ctx):
        if value not in config_groups and value is not None:
            self.fail(f"'{value}' is not a valid group. Choose from: {config_groups_str}", param, ctx)
        return value


@click.command()
@click.argument('group', type=ConfigGroup(), default=None, required=False)
@click.option('--reset', is_flag=True, help='Reset the configuration to default values.')
def configure(group, reset):
    """
    Run the configuration wizard to setup your environment.

    This command allows you to configure settings for your docketanalyzer environment.
    You can optionally specify a group to configure specific settings.

    Arguments:
    GROUP: The group of settings to configure. If not provided, all settings will be configured.
           Available groups: {groups}

    Options:
    --reset: Reset the configuration to default values before running the wizard.

    Example usage:
    da configure  # Configure all settings
    da configure mygroup  # Configure settings for 'mygroup'
    da configure --reset  # Reset all settings to default and reconfigure
    """
    docketanalyzer.config.update(reset=reset, group=group)


configure.__doc__ = configure.__doc__.format(groups=config_groups_str)

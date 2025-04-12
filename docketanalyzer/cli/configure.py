import click

from docketanalyzer import env

config_groups = list(set([key.group for key in env.keys.values() if key.group]))
config_groups_str = ", ".join(config_groups)
help_text = f"""
Configure your environment

GROUP: Optional filter for a group of config keys (one of: {config_groups_str}).

--reset: Reset your configuration to default values.
"""


class ConfigGroup(click.ParamType):
    """Custom click parameter type for validating configuration groups."""

    name = "group"

    def convert(self, value, param, ctx):
        """Convert the input value to a valid configuration group."""
        if value not in config_groups and value is not None:
            self.fail(
                f"'{value}' is not a valid group. Choose from: {config_groups_str}",
                param,
                ctx,
            )
        return value


@click.command(help=help_text)
@click.argument("group", type=ConfigGroup(), default=None, required=False)
@click.option(
    "--reset", is_flag=True, help="Reset the configuration to default values."
)
def configure(group, reset):
    """Run interactive configuration script."""
    env.configure(reset=reset, group=group)

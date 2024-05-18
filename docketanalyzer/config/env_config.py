from pathlib import Path
import simplejson as json
import os
from dotenv import load_dotenv


KEY_TYPES = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'path': lambda x: Path(x).resolve(),
}


CLI_INTRO = """

RUNNING CONFIGURATION SETUP

Any variables you set will be stored here:
%s

You can override these by including a .env in your working directory.

Press Ctrl+C to exit without saving.
Press Enter to keep the current value.
Use '*' to reset to the default value.
"""


class EnvConfig():
    def __init__(self, path, config_keys, cli_command, autoload_env=True):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.keys = config_keys
        self.cli_command = cli_command
        if autoload_env:
            load_dotenv(Path.cwd() / '.env', override=True)

    def load(self, skip_env=False):
        config = {}
        if self.path.exists():
            try:
                config = json.loads(self.path.read_text())
            except json.decoder.JSONDecodeError:
                self.path.unlink()
        for key in self.keys:
            value = None if skip_env else os.environ.get(key.name, None)
            if value is None:
                value = config.get(key.name, None)
            if value is not None:
                value = key.convert(value)
            config[key.name] = value
        return config

    def update_key(self, key, config, reset=False):
        current_value = None
        if not reset:
            current_value = config.get(key.name, None)
        prompt = key.name
        if current_value is not None:
            if key.mask:
                masked_value = str(current_value)
                mask_len = max([len(masked_value) - 4, 0])
                masked_value = '*' * mask_len + masked_value[mask_len:]
                prompt += ' [{}]'.format(masked_value)
            else:
                prompt += ' [{}]'.format(current_value)
        if key.description is not None:
            print(key.description)
        if key.default != '_' and key.default is not None:
            print("Defaults to: %s" % key.default)
        value = input(prompt + ': ')
        print()
        if not value:
            value = current_value
        elif value == '*':
            value = key.default
        else:
            try:
                value = key.convert(value)
            except ValueError as e:
                print("The value for '%s' must be of type '%s'" % (key.name, key.key_type))
                return self.update_key(key, config, reset=reset)

        config[key.name] = None if value is None else str(value)
        return config

    def update(self, group=None, reset=False):
        config = self.load(skip_env=True)
        try:
            print(CLI_INTRO % self.path)
            for key in self.keys:
                if key.group == group or group is None:
                    config = self.update_key(key, config, reset=reset)
            self.path.write_text(json.dumps(config, indent=2, default=str))
            print('Config saved to %s' % self.path)
        except KeyboardInterrupt:
            print('\nExiting without saving.')
            return

    def __getitem__(self, key_name):
        config = self.load()
        value = config.get(key_name, None)
        if value is None:
            keys = [x for x in self.keys if x.name == key_name]
            if len(keys) > 0:
                key = keys[0]
                if key.default != '_':
                    return key.default
                group = key.group or ''
                raise KeyError('The key "%s" is not in your configuration file, run "%s %s" to set value.' % (key_name, self.cli_command, group))
            else:
                raise KeyError('"%s" is not a valid configuration key' % key_name)
        return value

    def __str__(self):
        return str(self.load())


class ConfigKey():
    def __init__(self,
        name, group=None, key_type='str', description=None,
        default='_', mask=False,
    ):
        self.name = name
        self.group = group
        if key_type not in KEY_TYPES:
            raise ValueError('key_type must be one of %s' % ','.join(list(KEY_TYPES.keys())))
        self.key_type = key_type
        self.description = description
        self.default = default
        self.mask = mask

    def convert(self, value):
        return KEY_TYPES[self.key_type](value)
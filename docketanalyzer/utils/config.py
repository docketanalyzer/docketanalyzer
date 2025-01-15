from pathlib import Path
import simplejson as json
import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Callable, Union


KEY_TYPES: Dict[str, Callable] = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'path': lambda x: Path(x).resolve(),
}


CLI_INTRO = """

RUNNING CONFIGURATION SETUP

Any variables you set will be stored here:
{path}

You can override these by including a .env in your working directory.

Press Ctrl+C to exit without saving.
Press Enter to keep the current value.
Use '*' to reset to the default value.
"""


class Config():
    """
    Manages package configuration with support for environment variables, defaults,
    and persistent storage.

    | Features:
    | - Loads configuration from JSON file
    | - Supports environment variable overrides
    | - Automatic .env file loading
    | - Interactive CLI configuration
    | - Type validation for config values
    | - Support for masked sensitive values

    Args:
        path: Path to the JSON configuration file
        keys: List of ConfigKey objects defining valid configuration options
        autoload_env: Whether to automatically load .env file from current directory
    """
    def __init__(self, path: Union[str, Path], keys: List['ConfigKey'], autoload_env: bool = True) -> None:
        self.path: Path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.keys: Dict[str, 'ConfigKey'] = {}
        self.cache: Dict[str, Any] = {}
        if autoload_env:
            load_dotenv(Path.cwd() / '.env', override=True)
        for key in keys:
            self.register_key(key)
    
    def register_key(self, key: Union['ConfigKey', dict]) -> None:
        """Register a new configuration key.

        Args:
            key: ConfigKey object to register
        """
        if not isinstance(key, ConfigKey):
            key = ConfigKey(**key)
        self.keys[key.name] = key
        value = self.config[key.name]
        if value is not None:
            self.set(key.name, value)

    @property
    def alias_map(self) -> Dict[str, str]:
        """Returns a mapping of alias names to primary key names.
        
        Returns:
            dict: Mapping of alias names to their primary key names
        """
        if 'alias_map' not in self.cache:
            alias_map = {}
            for key in self.keys.values():
                for alias in key.alias_names:
                    alias_map[alias] = key.name
            self.cache['alias_map'] = alias_map
        return self.cache['alias_map']

    def load_stored_config(self) -> Dict[str, Any]:
        """Load configuration from the JSON file.
        
        Returns:
            dict: Stored configuration values
        
        Raises:
            json.JSONDecodeError: If the config file is invalid JSON
        """
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Failed to parse config file {self.path}: {str(e)}",
                    e.doc,
                    e.pos
                )
        return {}

    @property
    def config(self) -> Dict[str, Any]:
        """Get the complete configuration with all resolved values.
        
        Returns:
            dict: Complete configuration including environment variables and defaults
        """
        config = self.load_stored_config()
        for key in self.keys.values():
            value = os.environ.get(key.name, config.get(key.name))
            value = value if value is not None or not key.has_default else key.default
            try:
                config[key.name] = key.convert(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid value for {key.name}: {str(e)}")
        return config

    def configure_key(self, key: 'ConfigKey', config: Dict[str, Any], reset: bool = False) -> Optional[str]:
        """Configure a single key through interactive CLI.
        
        Args:
            key: ConfigKey object to configure
            config: Current configuration dict
            reset: Whether to ignore current value
            
        Returns:
            str or None: New value for the key, or None if unchanged
        """
        value = None if reset else config.get(key.name)
        prompt = f"{key.name}" + (f" [{key.display_value(value)}]" if value else '')
        if key.description is not None:
            print(key.description)
        if key.has_default:
            print(f"Defaults to: {key.default}")
        updated_value = input(prompt + ': ') or value
        if updated_value == '*': updated_value = key.default
        if updated_value:
            try:
                updated_value = key.convert(updated_value)
            except ValueError as e:
                print(f"The value for '{key.name}' must be of type '{key.key_type}'")
                return self.configure_key(key, config, reset=reset)
        return None if updated_value is None else str(updated_value)

    def configure(self, group: Optional[str] = None, reset: bool = False) -> None:
        """Run interactive configuration for all keys or a specific group.
        
        Args:
            group: Optional group name to configure only those keys
            reset: Whether to ignore current values
        """
        config = self.load_stored_config()
        try:
            print(CLI_INTRO.format(path=self.path))
            for key in self.keys.values():
                if key.group == group or group is None:
                    config[key.name] = self.configure_key(key, config, reset=reset)
            self.path.write_text(json.dumps(config, indent=2, default=str))
            print('Config saved to %s' % self.path)
        except KeyboardInterrupt:
            print('\nExiting without saving.')
    
    def set(self, name: str, value: Any) -> None:
        """Set a configuration value by adding it to your environment.
        
        Args:
            name: Key name or alias
            value: New value for the configuration key
        """
        name = self.alias_map.get(name, name)
        os.environ[name] = str(value)

    def add_to_namespace(self, namespace: dict) -> None:
        """Add all configuration keys to a namespace dictionary.
        
        Args:
            namespace: Dictionary to add configuration keys to
        """
        for key in self.keys.values():
            for name in [key.name] + key.alias_names:
                namespace[name] = self.config[key.name]

    
    def __getitem__(self, name: str) -> Any:
        """Get a configuration value by key name or alias.
        
        Args:
            name: Key name or alias
            
        Returns:
            Any: Configuration value from config file or environment variable
        """
        value = self.config.get(self.alias_map.get(name, name), None)
        return value or os.environ.get(name)
    
    def __getattr__(self, name):
        return self[name]

    def __str__(self):
        return str(json.dumps(self.config, indent=2, default=str))


class ConfigKey():
    """
    Defines a configuration key with its properties and validation rules.

    Args:
        name: Name of the configuration key
        group: Optional group for organizing related keys
        key_type: Type of the key value ('str', 'int', 'float', 'bool', 'path')
        description: Optional description for CLI help
        default: Default value, use '_' for no default
        mask: Whether to mask the value when displaying (for sensitive data)
        alias_names: List of alternative names for the key
    """
    def __init__(
        self,
        name: str,
        group: Optional[str] = None,
        key_type: str = 'str',
        description: Optional[str] = None,
        default: Any = '_',
        mask: bool = False,
        alias_names: List[str] = None,
    ) -> None:
        self.name = name
        self.alias_names = alias_names or []
        self.group = group
        if key_type not in KEY_TYPES:
            raise ValueError('key_type must be one of %s' % ','.join(list(KEY_TYPES.keys())))
        self.key_type = key_type
        self.description = description
        self.default = default
        self.mask = mask

    @property
    def has_default(self) -> bool:
        return self.default != '_'

    def display_value(self, value: Any) -> str:
        if self.mask:
            value = str(value)
            mask_len = max([len(value) - 4, 0])
            value = '*' * mask_len + value[mask_len:]
        return value

    def convert(self, value: Any) -> Any:
        if value is not None:
            return KEY_TYPES[self.key_type](value)
 
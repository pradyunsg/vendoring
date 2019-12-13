"""Loads configuration from pyproject.toml
"""

# mypy: allow-any-generics, allow-any-explicit

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple, Type, cast

from toml import TomlDecodeError
from toml import loads as parse_toml

from vendoring.errors import ConfigurationError
from vendoring.ui import UI


@dataclass
class Configuration:
    # Base directory for all of the operation of this project
    base_directory: Path

    # Location to unpack into
    target_dir: Path
    # Final namespace to rewrite imports to originate from
    target_namespace: str
    # Path to a pip-style requirement files
    requirements_path: Path
    # Filenames to ignore in target directory
    ignore_files: List[str]

    # Location to ``.patch` files to apply after vendoring
    patches_dir: Path
    # Additional substitutions to be made for imports
    additional_import_substitutions: List[Tuple[str, str]]
    # Additional substitutions to be made for imports
    target_drop_paths: List[str]

    # Whether licenses should be included
    include_licenses: bool
    # Fallbacks for licenses that can't be found
    license_fallback_urls: Dict[str, str]
    # Alternate directory names, where distribution name differs the installed name
    license_directories: Dict[str, str]

    # Whether typing stub files (.pyi) should be generated
    include_stubs: bool
    # Overrides for which stub files are generated
    stub_overrides: Dict[str, List[str]]

    @classmethod
    def load_from_dict(
        cls, dictionary: Dict[str, Any], *, location: Path
    ) -> "Configuration":
        """Constructs a Configuration, validating the values in `dictionary`, expecting paths to be within `location`.
        """

        def processor(
            *, default: Any, instance_of: Type, wrapper: Callable
        ) -> Callable:
            def func(key: str, di: Dict[str, Any]) -> Any:
                if key not in di:
                    if default is not None:
                        return default
                    raise ConfigurationError(f"Expected {key} to be provided")
                if not isinstance(di[key], instance_of):
                    raise ConfigurationError(f"Expected {key} to be {wrapper.__name__}")

                try:
                    retval = wrapper(di.pop(key))
                except ConfigurationError as e:
                    raise ConfigurationError(f"Invalid value for '{key}': {e}")

                return retval

            return func

        def path_wrapper(value: str) -> Path:
            path = Path(value)
            # Relative paths, are contained within location.
            if not path.is_absolute():
                return location / path
            # Absolute paths, must be within location.
            if location not in path.parents:
                raise ConfigurationError(f"Expected {path} to be in {location}")

            return path

        def list_of_tuple_with_two_str_wrapper(
            value: List[List[str]],
        ) -> List[Tuple[str, str]]:
            retval = []
            for elem in value:
                list_of_str_wrapper(elem)
                if len(elem) != 2:
                    raise ConfigurationError(
                        f"Expected exactly 2 values in tuple, got {len(elem)}."
                    )
                retval.append(cast(Tuple[str, str], tuple(elem)))
            return retval

        def list_of_str_wrapper(value: List[str]) -> List[str]:
            if not all(isinstance(elem, str) for elem in value):
                raise ConfigurationError(f"Expected list of strings.")
            return value

        def dict_wrapper(value_processor: Callable) -> Callable:
            def checker(di: Dict[str, Any]) -> Dict[str, Any]:
                for key in list(di.keys()):
                    di[key] = value_processor(key, di)
                return di

            return checker

        processors = {
            "path": processor(default=None, instance_of=str, wrapper=path_wrapper),
            "bool": processor(default=None, instance_of=bool, wrapper=bool),
            "bool_true": processor(default=True, instance_of=bool, wrapper=bool),
            "str": processor(default=None, instance_of=str, wrapper=str),
            "list_of_str": processor(
                default=[], instance_of=list, wrapper=list_of_str_wrapper,
            ),
            "list_of_tuple_with_two_str": processor(
                default=[],
                instance_of=list,
                wrapper=list_of_tuple_with_two_str_wrapper,
            ),
        }
        processors.update(
            {
                "dict_str": processor(
                    default=False,
                    instance_of=dict,
                    wrapper=dict_wrapper(value_processor=processors["str"],),
                ),
                "dict_list_of_str": processor(
                    default=False,
                    instance_of=dict,
                    wrapper=dict_wrapper(value_processor=processors["list_of_str"],),
                ),
            }
        )

        spec = {
            "target_dir": "path",
            "target_namespace": "str",
            "requirements_path": "path",
            "ignore_files": "list_of_str",
            "patches_dir": "path",
            "additional_import_substitutions": "list_of_tuple_with_two_str",
            "target_drop_paths": "list_of_str",
            "include_licenses": "bool",
            "license_fallback_urls": "dict_str",
            "license_directories": "dict_str",
            "include_stubs": "bool_true",
            "stub_overrides": "dict_list_of_str",
        }

        final_composition = {}
        for spec_key, p_type in spec.items():
            final_composition[spec_key] = processors[p_type](spec_key, dictionary)

        if dictionary:
            UI.warn(f"Got unknown keys: {list(dictionary)}")

        return cls(base_directory=location, **final_composition)


def load_configuration(directory: Path) -> Configuration:
    # Read the contents of the file.
    file = directory / "pyproject.toml"
    UI.log(f"Will attempt to load {file}.")

    try:
        file_contents = file.read_text(encoding="utf8")
    except IOError as read_error:
        raise ConfigurationError("Could not read pyproject.toml.") from read_error
    else:
        UI.log("Read configuration file.")

    try:
        parsed_contents = parse_toml(file_contents)
    except TomlDecodeError as toml_error:
        raise ConfigurationError("Could not parse pyproject.toml.") from toml_error
    else:
        UI.log("Parsed configuration file.")

    if (
        "tool" not in parsed_contents
        or not isinstance(parsed_contents["tool"], dict)
        or "vendoring" not in parsed_contents["tool"]
        or not isinstance(parsed_contents["tool"]["vendoring"], dict)
    ):
        raise ConfigurationError("Can not load `tool.vendoring` from pyproject.toml")

    tool_config = parsed_contents["tool"]["vendoring"]

    try:
        retval = Configuration.load_from_dict(tool_config, location=directory)
    except ConfigurationError as e:
        raise ConfigurationError(
            "Could not load values from [tool.vendoring] in pyproject.toml.\n"
            f"  REASON: {e}"
        )
    else:
        UI.log("Validated configuration.")
        return retval

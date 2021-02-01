"""Loads configuration from pyproject.toml
"""

# mypy: allow-any-generics, allow-any-explicit

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import ValidationError, validate
from toml import TomlDecodeError
from toml import loads as parse_toml

from vendoring.errors import ConfigurationError
from vendoring.ui import UI


@dataclass
class Configuration:
    # Base directory for all of the operation of this project
    base_directory: Path

    # Location to unpack into
    destination: Path
    # Final namespace to rewrite imports to originate from
    namespace: str
    # Path to a pip-style requirement files
    requirements: Path
    # Filenames to ignore in target directory
    protected_files: List[str]
    # Location to ``.patch` files to apply after vendoring
    patches_dir: Optional[Path]

    # Additional substitutions, done in addition to import rewriting
    substitute: List[Dict[str, str]]
    # Drop
    drop_paths: List[str]

    # Fallbacks for licenses that can't be found
    license_fallback_urls: Dict[str, str]
    # Alternate directory name, when distribution name differs from the package name
    license_directories: Dict[str, str]

    # Overrides for which stub files are generated
    typing_stubs: Dict[str, List[str]]

    @classmethod
    def load_from_dict(
        cls, dictionary: Dict[str, Any], *, location: Path
    ) -> "Configuration":
        """Constructs a Configuration, validating the values in `dictionary`, expecting paths to be within `location`."""

        schema = {
            "type": "object",
            "additionalProperties": False,
            "required": ["destination", "namespace", "requirements"],
            "properties": {
                "destination": {"type": "string"},
                "namespace": {"type": "string"},
                "requirements": {"type": "string"},
                "protected-files": {"type": "array", "items": {"type": "string"}},
                "patches-dir": {"type": "string"},
                "transformations": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "substitute": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["match", "replace"],
                                "properties": {
                                    "match": {"type": "string"},
                                    "replace": {"type": "string"},
                                },
                            },
                        },
                        "drop": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "license": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "directories": {
                            "type": "object",
                            "patternProperties": {"^.*$": {"type": "string"}},
                        },
                        "fallback-urls": {
                            "type": "object",
                            "patternProperties": {"^.*$": {"type": "string"}},
                        },
                    },
                },
                "typing-stubs": {
                    "type": "object",
                    "patternProperties": {
                        "^.*$": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
        }

        try:
            validate(dictionary, schema)
        except ValidationError as e:
            raise ConfigurationError(str(e))

        def path_or_none(key: str) -> Optional[Path]:
            if key in dictionary:
                return Path(dictionary[key])
            return None

        return Configuration(
            base_directory=location,
            destination=Path(dictionary["destination"]),
            namespace=dictionary["namespace"],
            requirements=Path(dictionary["requirements"]),
            protected_files=dictionary.get("protected-files", []),
            patches_dir=path_or_none("patches-dir"),
            substitute=dictionary.get("transformations", {}).get("substitute", {}),
            drop_paths=dictionary.get("transformations", {}).get("drop", []),
            license_fallback_urls=dictionary.get("license", {}).get(
                "fallback-urls", {}
            ),
            license_directories=dictionary.get("license", {}).get("directories", {}),
            typing_stubs=dictionary.get("typing-stubs", {}),
        )


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

"""Code for generating a Software Bill-of-Materials (SBOM)
from vendored libraries.
"""

import json
from pathlib import Path
from typing import Any, List
from urllib.parse import quote

from vendoring import __version__ as _vendoring_version
from vendoring.tasks.update import parse_pinned_packages as _parse_pinned_packages


def create_sbom_file(namespace: str, requirements: Path, sbom_file: Path) -> None:
    # The top-most name in the module namespace is the
    # most likely to be a recognizable name.
    top_level = namespace.split(".", 1)[0]
    top_level_bom_ref = f"bom-ref:{top_level}"
    components: List[Any] = [
        {"bom-ref": top_level_bom_ref, "name": top_level, "type": "library"}
    ]
    dependencies: List[Any] = [{"ref": top_level_bom_ref, "dependsOn": []}]
    sbom = {
        "$schema": "http://cyclonedx.org/schema/bom-1.4.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "tools": [{"name": "vendoring", "version": _vendoring_version}],
            "component": components[0],
        },
        "components": components,
        "dependencies": dependencies,
    }

    pkgs = sorted(
        _parse_pinned_packages(requirements), key=lambda item: (item.name, item.version)
    )
    for pkg in pkgs:
        purl = f"pkg:pypi/{quote(pkg.name, safe='')}@{quote(pkg.version, safe='')}"
        components.append(
            {
                "name": pkg.name,
                "version": pkg.version,
                "purl": purl,
                "type": "library",
                "bom-ref": purl,
            }
        )
        dependencies[0]["dependsOn"].append(purl)
        dependencies.append({"ref": purl})

    sbom_file.write_text(json.dumps(sbom, indent=2, sort_keys=True))

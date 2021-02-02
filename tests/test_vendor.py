"""Unit tests for `vendoring.tasks.vendor`"""

import textwrap
from vendoring.tasks.vendor import rewrite_file_imports


_SUPPORTED_IMPORT_FORMS = textwrap.dedent(
    """\
        import other
        from other import name1
        from other.name2 import name3
    """
)


class TestRewriteFileImports:
    def test_basic(self, tmp_path):
        path = tmp_path / "module.py"
        path.write_text(_SUPPORTED_IMPORT_FORMS)

        rewrite_file_imports(
            path,
            namespace="namespace",
            vendored_libs=["other"],
            additional_substitutions=[],
        )

        assert path.read_text() == textwrap.dedent(
            """\
                from namespace import other
                from namespace.other import name1
                from namespace.other.name2 import name3
            """
        )

    def test_does_not_rewrite_on_empty_namespace(self, tmp_path):
        path = tmp_path / "module.py"
        path.write_text(_SUPPORTED_IMPORT_FORMS)

        rewrite_file_imports(
            path,
            namespace="",
            vendored_libs=["other"],
            additional_substitutions=[],
        )

        assert path.read_text() == _SUPPORTED_IMPORT_FORMS

    def test_additional_substitutions_are_made(self, tmp_path):
        path = tmp_path / "module.py"
        path.write_text(_SUPPORTED_IMPORT_FORMS)

        rewrite_file_imports(
            path,
            namespace="namespace",
            vendored_libs=["other"],
            additional_substitutions=[{"match": r"name(\d)", "replace": r"NAME\1"}],
        )

        assert path.read_text() == textwrap.dedent(
            """\
                from namespace import other
                from namespace.other import NAME1
                from namespace.other.NAME2 import NAME3
            """
        )

    def test_additional_substitutions_are_made_on_empty_namespace(self, tmp_path):
        path = tmp_path / "module.py"
        path.write_text(_SUPPORTED_IMPORT_FORMS)

        rewrite_file_imports(
            path,
            namespace="",
            vendored_libs=["other"],
            additional_substitutions=[{"match": r"name(\d)", "replace": r"NAME\1"}],
        )

        assert path.read_text() == textwrap.dedent(
            """\
                import other
                from other import NAME1
                from other.NAME2 import NAME3
            """
        )

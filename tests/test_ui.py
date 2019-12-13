from unittest import mock

import pytest
from click import style

from vendoring.ui import _UserInterface


@pytest.fixture
def ui():
    retval = _UserInterface()
    with mock.patch.object(retval, "_log"):
        yield retval


@pytest.fixture
def verbose(ui):
    ui.verbose = True


def test_is_silent_by_default(ui):
    assert ui.verbose is False


def test_fixture_is_verbose(ui, verbose):
    assert ui.verbose is True


@pytest.mark.parametrize("verbosity", [True, False])
def test_shows_basic_log(ui, verbosity):
    ui.verbose = verbosity
    ui.log("blah")

    ui._log.assert_any_call("blah")


def test_shows_task_log_shown_when_verbose(ui, verbose):
    with ui.task("Task Name"):
        ui.log("blah")

    ui._log.assert_has_calls([mock.call("Task Name... ", nl=True), mock.call("  blah")])


def test_shows_task_log_redacted_when_silent(ui):
    with ui.task("Task Name"):
        ui.log("blah")

    ui._log.assert_any_call("Task Name... ", nl=False)

    # Ensure no calls made to log with the given message, since the task succeeded.
    assert mock.call("blah") not in ui._log.call_args_list
    assert mock.call("  blah") not in ui._log.call_args_list


def test_works_when_no_ui(ui):
    with ui.task("Task Name"):
        pass

    ui._log.assert_any_call("Task Name... ", nl=False)


def test_task_shows_spinner_when_silent(ui):
    with ui.task("Task Name"):
        ui.log("blah")
        ui.log("foo")
        ui.log("boo")

    assert ui._log.call_args_list == [
        mock.call("Task Name... ", nl=False),
        mock.call(ui._spinner_frames[0], nl=False, erase=True),
        mock.call(ui._spinner_frames[1], nl=False, erase=True),
        mock.call(ui._spinner_frames[2], nl=False, erase=True),
        mock.call(style("Done!", fg="green")),
    ]

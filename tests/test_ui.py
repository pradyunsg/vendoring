from unittest import mock

import pytest
from click import style

from vendoring.errors import VendoringError
from vendoring.ui import _UserInterface


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------
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


# --------------------------------------------------------------------------------------
# Actual Tests
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ["nl", "erase", "result"],
    [
        (False, True, mock.call("text\b\b\b\b", nl=False)),
        (True, True, AssertionError),
        (None, True, AssertionError),
        (False, False, mock.call("text", nl=False)),
        (True, False, mock.call("text", nl=True)),
        (None, False, mock.call("text", nl=True)),
        (False, None, mock.call("text", nl=False)),
        (True, None, mock.call("text", nl=True)),
        (None, None, mock.call("text", nl=True)),
    ],
)
def test__log_correctly_calls_click_echo(mocker, nl, erase, result):
    ui = _UserInterface()
    echo = mocker.patch("click.echo")

    kwargs = {"nl": nl, "erase": erase}
    # In this test, None means omit.
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if result is AssertionError:
        with pytest.raises(AssertionError):
            ui._log("text", **kwargs)
    else:
        ui._log("text", **kwargs)
        assert echo.call_args_list == [result]


def test_shows_basic_log(ui):
    ui.log("blah")
    ui._log.assert_any_call("blah")


def test_shows_basic_log_when_verbose(ui, verbose):
    ui.log("blah")
    ui._log.assert_any_call("blah")


@pytest.mark.parametrize("verbosity", [True, False])
def test_shows_basic_warn(ui, verbosity):
    ui.verbose = verbosity
    ui.warn("blah")

    ui._log.assert_any_call(style("WARN: blah", fg="yellow"))


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


def test_nested_tasks_not_allowed(ui):
    with pytest.raises(Exception, match="Only 1 task at a time."):
        with ui.task("First"):
            with ui.task("Second"):
                assert False, "should not get here"


def test_show_error(ui):
    try:
        raise Exception("Yay!")
    except Exception as e:
        ui.show_error(e)

    assert ui._log.call_args_list == [
        mock.call("  " + style("Yay!", fg="red")),
    ]


def test_show_error_verbose(ui, verbose):
    try:
        raise Exception("Yay!")
    except Exception as e:
        ui.show_error(e)

    assert ui._log.call_args_list == [
        # XXX: This contains the entire traceback. We should check this but I'm tired.
        mock.call(mock.ANY),
    ]


def test_task_failure(ui):
    # A failing task should raise the original error
    with pytest.raises(VendoringError, match="ABORT ABORT ABORT!"):
        with ui.task("Task Name"):
            ui.log("Houston, there's a problem!")

            raise VendoringError("ABORT ABORT ABORT!")

    # Make sure that the state of the UI isn't messed up (i.e. can enter a new task)
    with ui.task("Another Task"):
        ui.log("Works as expected")

    assert ui._log.call_args_list == [
        mock.call("Task Name... ", nl=False),
        mock.call("◴", nl=False, erase=True),
        mock.call(" "),
        mock.call("  Houston, there's a problem!"),
        mock.call("Another Task... ", nl=False),
        mock.call("◴", nl=False, erase=True),
        mock.call(style("Done!", fg="green")),
    ]


def test_task_failure_verbose(ui, verbose):
    # A failing task should raise the original error
    with pytest.raises(VendoringError, match="ABORT ABORT ABORT!"):
        with ui.task("Task Name"):
            ui.log("Houston, there's a problem!")

            raise VendoringError("ABORT ABORT ABORT!")

    # Make sure that the state of the UI isn't messed up (i.e. can enter a new task)
    with ui.task("Another Task"):
        ui.log("Works as expected")

    assert ui._log.call_args_list == [
        mock.call("Task Name... ", nl=True),
        mock.call("  Houston, there's a problem!"),
        mock.call("Another Task... ", nl=True),
        mock.call("  Works as expected"),
        mock.call("  " + style("Done!", fg="green")),
    ]

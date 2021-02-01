import shutil

import pytest

from vendoring.tasks.cleanup import cleanup_existing_vendored, determine_items_to_remove


@pytest.fixture
def throwaway(tmp_path):
    (tmp_path / "foo.txt").touch()
    (tmp_path / "bar.txt").touch()
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "baz.txt").touch()
    yield tmp_path
    shutil.rmtree(str(tmp_path))


class TestDetermineItemsToRemove:
    def test_non_existent_directory(self, tmp_path):
        locations = determine_items_to_remove(
            tmp_path / "non-existent",
            files_to_skip=[],
        )

        assert list(locations) == []

    @pytest.mark.parametrize(
        ["skip", "expected"],
        [
            ([], ["foo.txt", "bar.txt", "dir"]),
            (["dir"], ["foo.txt", "bar.txt", "dir"]),
            (["bar"], ["foo.txt", "bar.txt", "dir"]),
            (["bar.txt"], ["foo.txt", "dir"]),
            (["foo"], ["foo.txt", "bar.txt", "dir"]),
            (["foo.txt"], ["bar.txt", "dir"]),
            (["baz"], ["foo.txt", "bar.txt", "dir"]),
            (["baz.txt"], ["foo.txt", "bar.txt", "dir"]),
            (["foo.txt", "bar.txt"], ["dir"]),
        ],
    )
    def test_skipping(self, throwaway, skip, expected):
        locations = determine_items_to_remove(throwaway, files_to_skip=skip)

        got = []
        for item in locations:
            got.append(str(item.relative_to(throwaway)))

        assert sorted(got) == sorted(expected)


class TestCleanupExistingVendored:
    def test_calls_the_helper_correctly(self, mocker, tmp_path):
        our_unique_blob = object()

        # Mock out all the callees
        determine_mock = mocker.patch(
            "vendoring.tasks.cleanup.determine_items_to_remove"
        )
        determine_mock.return_value = our_unique_blob

        remove_mock = mocker.patch("vendoring.tasks.cleanup.remove_all")

        # Create a mock to pass in
        config_mock = mocker.Mock()
        config_mock.destination = tmp_path
        config_mock.protected_files = []

        # The actual thing we're testing
        cleanup_existing_vendored(config_mock)

        # Make sure the things we wanted happened
        determine_mock.assert_called_with(tmp_path, files_to_skip=[])
        remove_mock.assert_called_with(our_unique_blob)

    def test_functional(self, mocker, throwaway):
        config_mock = mocker.Mock()
        config_mock.destination = throwaway
        config_mock.protected_files = ["foo.txt"]

        cleanup_existing_vendored(config_mock)

        assert sorted(throwaway.iterdir()) == [throwaway / "foo.txt"]

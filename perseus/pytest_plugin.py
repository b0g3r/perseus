import os

import pytest
import re

from _pytest.capture import CaptureManager

from perseus._vendor.snapshottest.error import SnapshotNotFound
from perseus._vendor.snapshottest.formatter import Formatter
from perseus._vendor.snapshottest.module import SnapshotModule, SnapshotTest
from perseus._vendor.snapshottest.diff import PrettyDiff
from perseus._vendor.snapshottest.reporting import diff_report

def _pytest_input(prompt):
    with os.fdopen(os.dup(1), "w") as stdout:
        stdout.write("\n{}? ".format(prompt))

    with os.fdopen(os.dup(2), "r") as stdin:
        return stdin.readline()

def pytest_addoption(parser):
    group = parser.getgroup("perseus")
    group.addoption(
        "--perseus-update",
        action="store_true",
        dest='perseus-update',
        default=False,
        help='If some snapshot is failed, update it via interactive prompt',
    )

# TODO: interactive prompt if it is first catch
# TODO: interactive prompt if snapshot is different from value


class PyTestSnapshotTest(SnapshotTest):
    def __init__(self, request=None):
        self.request = request
        super(PyTestSnapshotTest, self).__init__()

    @property
    def module(self):
        return SnapshotModule.get_module_for_testpath(self.request.node.fspath.strpath)

    @property
    def test_name(self):
        cls_name = getattr(self.request.node.cls, "__name__", "")
        flattened_node_name = re.sub(
            r"\s+", " ", self.request.node.name.replace(r"\n", " ")
        )
        return "{}{} {}".format(
            "{}.".format(cls_name) if cls_name else "",
            flattened_node_name,
            self.curr_snapshot,
        )

    def assert_match(self, value, name=''):
        self.curr_snapshot = name or self.snapshot_counter
        self.visit()
        try:
            prev_snapshot = self.module[self.test_name]
        except SnapshotNotFound:
            self.store(value)  # first time this test has been seen
        else:
            try:
                self.assert_value_matches_snapshot(value, prev_snapshot)
            except AssertionError:
                cm: CaptureManager = self.request.config.pluginmanager.getplugin("capturemanager")
                cm.suspend_global_capture(in_=True)
                print(*diff_report(PrettyDiff(value, self), prev_snapshot), sep='\n')
                inp = input('Replace with new value? [y]/n: ')
                cm.resume_global_capture()
                if inp.lower() == 'n':
                    self.fail()
                    raise
                else:
                    self.store(value)
        if not name:
            self.snapshot_counter += 1


@pytest.fixture
def snapshot(request):
    with PyTestSnapshotTest(request) as snapshot_test:
        yield snapshot_test


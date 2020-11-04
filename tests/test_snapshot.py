from importlib import reload
from pathlib import Path
from typing import (
    Any,
    List,
    Tuple,
)

import pytest
from _pytest.config import ExitCode
from _pytest.pathlib import make_numbered_dir
from _pytest.pytester import (
    RunResult,
    Testdir,
)

from perseus._vendor.snapshottest import Snapshot


class PerseusTester(Testdir):
    """
    Son of pytest's Testdir, but with hacks around stdin and checking snapshots.
    """

    def prepare_sample(self, sample_name) -> Any:
        """
        Helper, which copying sample into temp dir and imports snapshot file.
        """
        sample_dir = self.copy_example(sample_name)
        snapshot_path = sample_dir.join('snapshots', 'snap_test_{0}.py'.format(sample_name))
        return snapshot_path.pyimport()

    def runpytest_subprocess(self, *args, **kwargs) -> RunResult:
        """
        Allow to pass stdin into ``run``.
        """
        __tracebackhide__ = True
        p = make_numbered_dir(root=Path(str(self.tmpdir)), prefix="runpytest-")
        args = ("--basetemp=%s" % p,) + args
        plugins = [x for x in self.plugins if isinstance(x, str)]
        if plugins:
            args = ("-p", plugins[0]) + args
        args = self._getpytestargs() + args
        return self.run(*args, **kwargs)

    def run_perseus(
        self,
        sample_name: str,
        inputs: List[str],
    ) -> Tuple[RunResult, Snapshot, Snapshot]:
        """
        Prepare sample, get sample snapshots, run perseus with given inputs and get new snapshots.
        """
        snapshot_module = self.prepare_sample(sample_name)
        old_snapshots = snapshot_module.snapshots
        run_result = self.runpytest_subprocess(stdin='\n'.join(inputs).encode('utf-8'))
        reload(snapshot_module)
        new_snapshots = snapshot_module.snapshots
        return run_result, old_snapshots, new_snapshots


@pytest.fixture()
def tester(request, tmpdir_factory):
    return PerseusTester(request, tmpdir_factory)


def test_reject_replacing(tester: PerseusTester):
    run_result, old_snapshots, new_snapshots = tester.run_perseus(
        sample_name='one_good_one_bad',
        inputs=['n'],
    )
    assert run_result.ret == ExitCode.TESTS_FAILED
    assert old_snapshots == new_snapshots


def test_agree_replacing(tester: PerseusTester):
    run_result, old_snapshots, new_snapshots = tester.run_perseus(
        sample_name='one_good_one_bad',
        inputs=['y'],
    )
    assert run_result.ret == ExitCode.OK
    assert old_snapshots != new_snapshots


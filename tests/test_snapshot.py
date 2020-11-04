import sys
import traceback
from importlib import reload
from io import UnsupportedOperation
from pathlib import Path
from typing import (
    Any,
    List,
    Tuple,
)

import pytest
from _pytest import timing
from _pytest.capture import (
    DontReadFromInput,
    MultiCapture,
    SysCapture,
)
from _pytest.config import ExitCode
from _pytest.pathlib import make_numbered_dir
from _pytest.pytester import (
    RunResult,
    Testdir,
)

from perseus._vendor.snapshottest import Snapshot


class ReadFromInput(DontReadFromInput):
    encoding = 'utf-8'

    def __init__(self, stdin=None):
        inputs = stdin.decode(self.encoding).split('\n') if stdin else []
        self.input_count = len(inputs)
        self.inputs = iter(inputs)

    def read(self, *args):
        try:
            return next(self.inputs)
        except StopIteration:
            raise RuntimeError(
                f'Attempt to read more inputs than were provided ({self.input_count} was provided)'
            )

    readline = read
    readlines = read
    __next__ = read


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

    def runpytest_inprocess(self, *args, stdin=None, **kwargs) -> RunResult:
        """
        Same as Testdir.runpytest_inprocess, but with support of stdin.
        Yes, it's ugly :(

        Return result of running pytest in-process, providing a similar
        interface to what self.runpytest() provides."""
        __tracebackhide__ = True
        syspathinsert = kwargs.pop("syspathinsert", False)

        if syspathinsert:
            self.syspathinsert()
        now = timing.time()
        input_reader = ReadFromInput(stdin)
        capture = MultiCapture(
            in_=SysCapture(0, tmpfile=input_reader), out=SysCapture(1), err=SysCapture(2)
        )
        capture.start_capturing()
        try:
            try:
                reprec = self.inline_run(*args, **kwargs)
            except SystemExit as e:
                ret = e.args[0]
                try:
                    ret = ExitCode(e.args[0])
                except ValueError:
                    pass

                class reprec:  # type: ignore
                    ret = ret
            except Exception:
                traceback.print_exc()

                class reprec:  # type: ignore
                    ret = ExitCode(3)

        finally:
            out, err = capture.readouterr()
            capture.stop_capturing()
            sys.stdout.write(out)
            sys.stderr.write(err)

        assert reprec.ret is not None
        res = RunResult(
            reprec.ret, out.splitlines(), err.splitlines(), timing.time() - now
        )
        res.reprec = reprec  # type: ignore
        return res

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
        run_result = self.runpytest(stdin='\n'.join(inputs).encode('utf-8'))
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

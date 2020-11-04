from _pytest.config import ExitCode

from tests.conftest import PerseusTester


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

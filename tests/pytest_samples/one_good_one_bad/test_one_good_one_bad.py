def test_one_good_one_bad(snapshot):
    assert snapshot.match('one like in snapshot')
    assert snapshot.match('0n3 n0t l1k3 1n sn5psh0t')

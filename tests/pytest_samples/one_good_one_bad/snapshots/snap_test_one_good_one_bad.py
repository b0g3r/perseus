# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from perseus._vendor.snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_one_good_one_bad 1'] = 'one like in snapshot'
snapshots['test_one_good_one_bad 2'] = 'one not like in snapshot'

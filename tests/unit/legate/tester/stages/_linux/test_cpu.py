# Copyright 2022 NVIDIA Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Consolidate test configuration from command-line and environment.

"""
from __future__ import annotations

import pytest

from legate.tester.config import Config
from legate.tester.stages._linux import cpu as m
from legate.tester.stages.util import UNPIN_ENV

from .. import FakeSystem

unpin_and_test = dict(UNPIN_ENV)


def test_default() -> None:
    c = Config([])
    s = FakeSystem(cpus=12)
    stage = m.CPU(c, s)
    assert stage.kind == "cpus"
    assert stage.args == []
    assert stage.env(c, s) == unpin_and_test
    assert stage.spec.workers > 0

    shard = (1, 2, 3)
    assert "--cpu-bind" in stage.shard_args(shard, c)


def test_cpu_pin_strict() -> None:
    c = Config(["test.py", "--cpu-pin", "strict"])
    s = FakeSystem(cpus=12)
    stage = m.CPU(c, s)
    assert stage.kind == "cpus"
    assert stage.args == []
    assert stage.env(c, s) == {}
    assert stage.spec.workers > 0

    shard = (1, 2, 3)
    assert "--cpu-bind" in stage.shard_args(shard, c)


def test_cpu_pin_none() -> None:
    c = Config(["test.py", "--cpu-pin", "none"])
    s = FakeSystem(cpus=12)
    stage = m.CPU(c, s)
    assert stage.kind == "cpus"
    assert stage.args == []
    assert stage.env(c, s) == unpin_and_test
    assert stage.spec.workers > 0

    shard = (1, 2, 3)
    assert "--cpu-bind" not in stage.shard_args(shard, c)


@pytest.mark.parametrize("shard,expected", [[(2,), "2"], [(1, 2, 3), "1,2,3"]])
def test_shard_args(shard: tuple[int, ...], expected: str) -> None:
    c = Config([])
    s = FakeSystem()
    stage = m.CPU(c, s)
    result = stage.shard_args(shard, c)
    assert result == ["--cpus", f"{c.cpus}", "--cpu-bind", expected]


def test_spec_with_cpus_1() -> None:
    c = Config(["test.py", "--cpus", "1"])
    s = FakeSystem()
    stage = m.CPU(c, s)
    assert stage.spec.workers == 3
    assert stage.spec.shards == [(0, 1), (2, 3), (4, 5)]


def test_spec_with_cpus_2() -> None:
    c = Config(["test.py", "--cpus", "2"])
    s = FakeSystem()
    stage = m.CPU(c, s)
    assert stage.spec.workers == 2
    assert stage.spec.shards == [(0, 1, 2), (3, 4, 5)]


def test_spec_with_utility() -> None:
    c = Config(["test.py", "--cpus", "1", "--utility", "2"])
    s = FakeSystem()
    stage = m.CPU(c, s)
    assert stage.spec.workers == 2
    assert stage.spec.shards == [(0, 1, 2), (3, 4, 5)]


def test_spec_with_requested_workers() -> None:
    c = Config(["test.py", "--cpus", "1", "-j", "2"])
    s = FakeSystem()
    stage = m.CPU(c, s)
    assert stage.spec.workers == 2
    assert stage.spec.shards == [(0, 1), (2, 3)]


def test_spec_with_requested_workers_zero() -> None:
    s = FakeSystem()
    c = Config(["test.py", "-j", "0"])
    assert c.requested_workers == 0
    with pytest.raises(RuntimeError):
        m.CPU(c, s)


def test_spec_with_requested_workers_bad() -> None:
    s = FakeSystem()
    c = Config(["test.py", "-j", f"{len(s.cpus)+1}"])
    assert c.requested_workers > len(s.cpus)
    with pytest.raises(RuntimeError):
        m.CPU(c, s)


def test_spec_with_verbose() -> None:
    args = ["test.py", "--cpus", "2"]
    c = Config(args)
    cv = Config(args + ["--verbose"])
    s = FakeSystem()

    spec, vspec = m.CPU(c, s).spec, m.CPU(cv, s).spec
    assert vspec == spec

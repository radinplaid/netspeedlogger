#!/usr/bin/env python
"""Tests for `netspeedlogger` package."""
# pylint: disable=redefined-outer-name

import builtins
import logging
import os
from tempfile import TemporaryDirectory

import mock
import numpy as np
import pandas as pd
import pytest
from faker import Faker

tempdir = TemporaryDirectory()
os.environ["NETSPEEDLOGGER"] = tempdir.name


@pytest.fixture
def speedtest_result():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    fake = Faker()
    results_dict = {
        "download": fake.random.random() * 1000,
        "upload": fake.random.random() * 1000,
        "bytes_sent": fake.random.randint(100, 10000),
        "bytes_received": fake.random.randint(100, 10000),
        "ping": fake.random.random() * 100,
        "server": {"host": fake.name(), "id": str(fake.random.randint(1, 1000))},
        "timestamp": str(fake.date_time()),
    }
    return results_dict


def test_validate_speedtest_result(speedtest_result):
    """Sample pytest test function with the pytest fixture as an argument."""
    from ..netspeedlogger.netspeedlogger import validate_speedtest_result

    validate_speedtest_result(speedtest_result)


def test_run_speedtest_timeout_zero():
    """Sample pytest test function with the pytest fixture as an argument."""
    from ..netspeedlogger.netspeedlogger import (
        run_speedtest,
        speedtest_dict_to_dataframe,
    )

    speedtest_result = run_speedtest(timeout=0, retries=1)
    df = speedtest_dict_to_dataframe(speedtest_result)
    assert df["download_speed"].values[0] == 0
    assert df["upload_speed"].values[0] == 0
    assert df["bytes_sent"].values[0] == 0
    assert df["bytes_received"].values[0] == 0
    assert df["ping"].values[0] is None
    assert df["server_host"].values[0] is None
    assert df["server_id"].values[0] is None


def test_cli_run(capsys):
    from ..netspeedlogger.cli import speedtest

    speedtest()
    captured = capsys.readouterr()
    assert "netspeedlogger speedtest" in captured.out
    assert (
        "Starting to run an internet speed test, and logging the output" in captured.out
    )
    assert "Speedtest complete." in captured.out


def test_cli_summary(capsys):
    from ..netspeedlogger.cli import summary

    summary()
    captured = capsys.readouterr()
    assert "count" in captured.out
    assert "mean" in captured.out
    assert "Download Speed (Mb/s)" in captured.out
    assert "Upload Speed (Mb/s)" in captured.out
    assert "Ping (ms)" in captured.out


def test_cli_results(capsys):
    from ..netspeedlogger.cli import results

    results()
    captured = capsys.readouterr()
    assert "Date Time" in captured.out
    assert "Download Speed (Mb/s)" in captured.out
    assert "Upload Speed (Mb/s)" in captured.out
    assert "Ping (ms)" in captured.out


def test_create_speedtest_dir():
    """If netspeedloggerdir does not exist, create it"""
    from ..netspeedlogger.netspeedlogger import get_database_path

    os.environ["NETSPEEDLOGGER"] = os.path.join(tempdir.name, "test")
    assert os.path.isdir(os.path.join(tempdir.name, "test"))


def test_delete_database_n():
    from ..netspeedlogger.cli import delete_database

    with mock.patch.object(builtins, "input", lambda _: "n"):
        assert delete_database() == "Not deleting database"


def test_delete_database_y():
    from ..netspeedlogger.cli import delete_database, get_database_path

    dbpath = get_database_path()
    dbexists = os.path.isfile(dbpath)
    with mock.patch.object(builtins, "input", lambda _: "y"):
        assert delete_database() == "Database deleted"

    # If there was a database, assert it was deleted
    if dbexists:
        assert os.path.isfile(dbpath) is False

#!/usr/bin/env python
"""Tests for `netspeedlogger` package."""
# pylint: disable=redefined-outer-name

import builtins
import logging
import os
from tempfile import TemporaryDirectory

import mock
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


def test_database_has_results():
    from ..netspeedlogger.netspeedlogger import database_has_results

    assert database_has_results() is False


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


def test_selectall_with_date_range_noresults():
    from ..netspeedlogger.netspeedlogger import selectall_with_date_range

    df = selectall_with_date_range("2020-01-01 00:00:00", "2050-01-01 00:00:00")
    assert df is None


def test_cli_run(capsys):
    from ..netspeedlogger.cli import speedtest

    speedtest()
    captured = capsys.readouterr()
    assert "netspeedlogger speedtest" in captured.out
    assert (
        "Starting to run an internet speed test, and logging the output" in captured.out
    )
    assert "Speedtest complete." in captured.out


def test_altair_timeseries_chart():
    from ..netspeedlogger.netspeedlogger import (
        timeseries_chart,
        selectall_with_date_range,
    )
    import datetime
    import altair as alt

    min_date = datetime.date.today() - datetime.timedelta(days=7)
    max_date = datetime.date.today() + datetime.timedelta(days=1)

    dat = selectall_with_date_range(min_date=str(min_date), max_date=str(max_date))

    if isinstance(dat, pd.DataFrame):
        dat["download_speed"] = dat["download_speed"] / (1024 * 1024)
        dat["upload_speed"] = dat["upload_speed"] / (1024 * 1024)
        dat["hour"] = [int(i[11:13]) for i in dat["timestamp"]]

        chart = timeseries_chart(dat, "ping", 1000, 2000)

        assert isinstance(chart, alt.Chart)
    else:
        assert dat is None


def test_cli_summary(capsys):
    from ..netspeedlogger.cli import summary
    from ..netspeedlogger.netspeedlogger import database_has_results

    summary()
    captured = capsys.readouterr()

    if database_has_results():
        assert "count" in captured.out
        assert "mean" in captured.out
        assert "Download Speed (Mb/s)" in captured.out
        assert "Upload Speed (Mb/s)" in captured.out
        assert "Ping (ms)" in captured.out
    else:
        assert "No results - run `netspeedlogger run` first" in captured.out


def test_cli_results(capsys):
    from ..netspeedlogger.cli import results
    from ..netspeedlogger.netspeedlogger import database_has_results

    results()
    captured = capsys.readouterr()

    if database_has_results():
        assert "Date Time" in captured.out
        assert "Download Speed (Mb/s)" in captured.out
        assert "Upload Speed (Mb/s)" in captured.out
        assert "Ping (ms)" in captured.out
    else:
        assert "No results - run `netspeedlogger run` first" in captured.out


def test_selectall_with_date_range():
    from ..netspeedlogger.netspeedlogger import (
        selectall_with_date_range,
        database_has_results,
    )

    df = selectall_with_date_range("2020-01-01 00:00:00", "2050-01-01 00:00:00")

    if database_has_results():
        assert isinstance(df, pd.DataFrame)
    else:
        assert df is None


def test_delete_database_n():
    from ..netspeedlogger.cli import delete_database
    from ..netspeedlogger.netspeedlogger import database_has_results

    if database_has_results():
        with mock.patch.object(builtins, "input", lambda _: "n"):
            assert delete_database() == "Not deleting database"
    else:
        pass


def test_delete_database_y():
    from ..netspeedlogger.cli import delete_database, database_has_results
    from ..netspeedlogger.netspeedlogger import get_database_path

    if database_has_results():
        dbpath = get_database_path()
        with mock.patch.object(builtins, "input", lambda _: "y"):
            assert delete_database() == "Database deleted"
            assert os.path.isfile(dbpath) is False
    else:
        pass

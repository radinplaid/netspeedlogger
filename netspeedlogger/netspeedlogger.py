import datetime
import logging
import os
import sqlite3
from time import sleep

import altair as alt
import pandas as pd
import speedtest

mylogger = logging.getLogger("netspeedlogger")

# For the odroid
# os.environ["NETSPEEDLOGGER"] = "/media/externalssd/"


def get_database_path():
    """Returns the path to the netspeedlogger sqlite database

    Set the env var NETSPEEDLOGGER to change the default folder location

    If NETSPEEDLOGGER is not set, it is stored here: ~/.netspeedlogger/netspeedlogger.sqlite3
    If the folder .netspeedlogger doesn't exist, it will be created
    """
    USERHOME = os.path.expanduser("~")

    database_folder = os.environ.get(
        "NETSPEEDLOGGER", os.path.join(USERHOME, ".netspeedlogger")
    )

    if not os.path.isdir(database_folder):
        os.makedirs(database_folder, exist_ok=True)

    return os.path.join(database_folder, "netspeedlogger.sqlite3")


def database_has_results():
    """Returns True if netspeedlogger database has results, False otherwise"""
    result = query("select count(*) from netspeedlogger")
    if isinstance(result, pd.DataFrame):
        return True
    else:
        return False


def query(query: str):
    """Run a SQL querry on the netspeedlogger database"""
    database_file = get_database_path()
    if os.path.isfile(database_file):
        con = sqlite3.connect(database_file)
        df = pd.read_sql_query(query, con)
        con.close()
        return df
    else:
        return None


def selectall():
    """Select all records in the netspeedlogger database"""
    return query("SELECT * from netspeedlogger")


def validate_speedtest_result(results_dict: dict):
    """Validates speedtest-cli results results_dict has required fields"""
    mylogger.info("Validating response before inserting into database")
    assert "download" in results_dict
    assert "upload" in results_dict
    assert "bytes_sent" in results_dict
    assert "bytes_received" in results_dict
    assert "ping" in results_dict
    assert "server" in results_dict
    assert "host" in results_dict["server"]
    assert "id" in results_dict["server"]
    assert isinstance(results_dict["download"], float)
    assert isinstance(results_dict["upload"], float)
    assert isinstance(results_dict["bytes_sent"], int)
    assert isinstance(results_dict["bytes_received"], int)
    assert isinstance(results_dict["ping"], float)
    assert isinstance(results_dict["server"]["host"], str)
    assert isinstance(results_dict["server"]["id"], str)


def speedtest_dict_to_dataframe(results_dict):
    """Converts speedtest-cli results_dict to a pandas.DataFrame"""
    return pd.DataFrame(
        [
            {
                "download_speed": results_dict["download"],
                "upload_speed": results_dict["upload"],
                "bytes_sent": results_dict["bytes_sent"],
                "bytes_received": results_dict["bytes_received"],
                "ping": results_dict["ping"],
                "server_host": results_dict["server"]["host"],
                "server_id": results_dict["server"]["id"],
                "timestamp": str(datetime.datetime.now()),
            }
        ]
    )


def write_speedtest_to_database(df: pd.DataFrame):
    """Write speedtest result to netspeedlogger database"""
    database_path = get_database_path()
    mylogger.info(f"Opening database: {database_path}")
    con = sqlite3.connect(database_path)

    mylogger.info("Inserting into database")
    df.to_sql("netspeedlogger", con, if_exists="append")

    mylogger.info(str(datetime.datetime.now()))
    mylogger.info("Internet Speed Test script finished")
    con.close()


def delete_database_if_exists():
    """Delete netspeedlogger database if it exists"""
    dbpath = get_database_path()
    if os.path.isfile(dbpath):
        os.remove(dbpath)


def run_speedtest(retries: int = 3, timeout: int = 15, sleep_between_retries: int = 10):
    """Run internet speed test with speedtest-cli library"""
    for retry_count in range(retries):
        try:
            s = speedtest.Speedtest(timeout=timeout)
            s.get_best_server()
            s.download(threads=None)
            s.upload(threads=None)
            results_dict = s.results.dict()
            validate_speedtest_result(results_dict)
            return results_dict
        except speedtest.ConfigRetrievalError as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            mylogger.warning(message)
            if (retry_count + 1) < retries:
                sleep(sleep_between_retries)
        except IndexError as e:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            mylogger.warning(message)
            if (retry_count + 1) < retries:
                sleep(sleep_between_retries)

    mylogger.error(f"Failed running speed test {retries} times; returning zero values")

    return {
        "download": 0,
        "upload": 0,
        "bytes_sent": 0,
        "bytes_received": 0,
        "ping": None,
        "server": {"host": None, "id": None},
        "timestamp": str(datetime.datetime.now()),
    }


def selectall_with_date_range(min_date, max_date):
    """Select all from netspeedlogger database with date range"""
    return query(
        f"SELECT * FROM netspeedlogger where timestamp >= '{min_date}' and timestamp <= '{max_date}'"
    )


def timeseries_chart(dat, variable, CHART_HEIGHT, CHART_WIDTH):
    """Altair timeseries chart for netspeedlogger"""
    return (
        alt.Chart(dat, title="")
        .mark_line(interpolate="cardinal", point=alt.OverlayMarkDef())
        .encode(
            x="timestamp:T",
            y=f"{variable}:Q",
            tooltip=[
                alt.Tooltip(variable, title=variable),
                alt.Tooltip("timestamp:T", title="Date"),
                alt.Tooltip("timestamp:T", title="Hour", timeUnit="hours"),
                alt.Tooltip("timestamp:T", title="Minute", timeUnit="minutes"),
            ],
        )
        .properties(height=CHART_HEIGHT, width=CHART_WIDTH)
    )

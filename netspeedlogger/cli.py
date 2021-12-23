"""Console script for netspeedlogger."""

import os
import pathlib
import sys

import fire
import pandas as pd
from streamlit import cli as stcli

from .netspeedlogger import (
    database_has_results,
    delete_database_if_exists,
    get_database_path,
    query,
    run_speedtest,
    speedtest_dict_to_dataframe,
    write_speedtest_to_database,
)


def sql_to_markdown(sql_query: str, showindex: bool = False):
    """Run a SQL querry on the netspeedlogger database and print a table of the results"""

    if database_has_results():
        df = query(sql_query)
        print(df.to_markdown(index=showindex))
    else:
        print("No results - run `netspeedlogger run` first")


def results():
    """Show all results from the netspeedlogger database

    If there are more than 10000 results, will show the first 10000
    """
    sql_to_markdown(
        "select substr(timestamp,1,19) as 'Date Time', "
        "   download_speed/(1024*1024) as 'Download Speed (Mb/s)', "
        "   upload_speed/(1024*1024) as 'Upload Speed (Mb/s)', "
        "   bytes_sent/(1024) as 'kB Sent', "
        "   bytes_received/(1024) as 'kB Recieved', "
        "   server_id  as 'Server ID', "
        "   server_host as 'Server Host', "
        "   ping as 'Ping (ms)'  "
        "   from netspeedlogger limit 10000"
    )


def summary():
    """Display summary of internet speed test results as a table"""
    if database_has_results():
        df = query(
            (
                "select substr(timestamp,1,19) as 'Date Time', "
                "   download_speed/(1024*1024) as 'Download Speed (Mb/s)', "
                "   upload_speed/(1024*1024) as 'Upload Speed (Mb/s)', "
                "   ping as 'Ping (ms)'  "
                "   from netspeedlogger "
            )
        )
        print(df.describe().to_markdown(index=True))
    else:
        print("No results - run `netspeedlogger run` first")


def speedtest():
    """Run an internet speed test using speedtest-cli and save the results to a local sqlite database"""
    print("netspeedlogger speedtest")
    print("=" * len("netspeedlogger speedtest"))
    print("Starting to run an internet speed test, and logging the output")

    results_dict = run_speedtest()
    df = speedtest_dict_to_dataframe(results_dict)
    write_speedtest_to_database(df)
    print("Speedtest complete. Results:")
    print(df.to_markdown(index=False))


def app():
    streamlit_app_path = os.path.join(
        pathlib.Path(__file__).parent.resolve(), "app.py"
    )  # pragma: no cover
    sys.argv = ["streamlit", "run", streamlit_app_path]  # pragma: no cover
    sys.exit(stcli.main())  # pragma: no cover


def delete_database():
    """Run a SQL querry on the netspeedlogger database and print a table of the results"""
    db_path = get_database_path()
    print(f"Deleting netspeedlogger database at path: `{db_path}`")
    print(
        "Are you sure you want to delete the whole database? Input 'y' for yes or 'n' for no"
    )

    for i in range(10):
        confirmation = input("Please type 'y' for Yes or 'n' for No")
        if confirmation == "n":
            return "Not deleting database"
        elif confirmation == "y":
            delete_database_if_exists()
            return "Database deleted"


def main():
    fire.Fire(
        {
            "speedtest": speedtest,
            "results": results,
            "summary": summary,
            "app": app,
            "delete_database": delete_database,
        }
    )


if __name__ == "__main__":
    main()  # pragma: no cover

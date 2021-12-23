import datetime
import logging
import os
import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")
st.title("Internet Speed Test Results")

netspeedlogger = logging.getLogger("netspeedlogger")

# Database is stored in ~/.netspeedlogger/netspeedlogger.sqlite3
USERHOME = os.path.expanduser("~")
NETSPEEDLOGGER_DIR = os.environ.get(
    "NETSPEEDLOGGER", os.path.join(USERHOME, ".netspeedlogger")
)
os.makedirs(NETSPEEDLOGGER_DIR, exist_ok=True)
database_file = os.path.join(NETSPEEDLOGGER_DIR, "netspeedlogger.sqlite3")

netspeedlogger.info("Speed Test script started")
netspeedlogger.info(str(datetime.datetime.now()))

CHART_WIDTH = 1600
CHART_HEIGHT = 400


def selectall(min_date, max_date, database_file=database_file):
    con = sqlite3.connect(database_file)
    df = pd.read_sql_query(
        f"SELECT * FROM netspeedlogger where timestamp >= '{min_date}' and timestamp <= '{max_date}'",
        con=con,
    )
    con.close()
    return df


min_date = datetime.date.today() - datetime.timedelta(days=7)
max_date = datetime.date.today() + datetime.timedelta(days=1)

a_date = st.date_input("Pick a date", (min_date, max_date))
dat = selectall(min_date=str(a_date[0]), max_date=str(a_date[1]))

dat["download_speed"] = dat["download_speed"] / (1024 * 1024)
dat["upload_speed"] = dat["upload_speed"] / (1024 * 1024)
dat["hour"] = [int(i[11:13]) for i in dat["timestamp"]]


def timeseries_chart(variable):
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


st.subheader("Download Speed (Mb/s)")
st.altair_chart(timeseries_chart("download_speed"))

col1, col2, col3 = st.columns(3)

col1.altair_chart(
    alt.Chart(dat, title="Download Speed by Hour(Mb/s)")
    .mark_boxplot(extent="min-max")
    .encode(x="hour:O", y="download_speed:Q")
    .properties(height=CHART_HEIGHT, width=CHART_WIDTH / 3 - 50)
)

col2.altair_chart(
    alt.Chart(dat, title="Upload Speed by Hour (Mb/s)")
    .mark_boxplot(extent="min-max")
    .encode(x="hour:O", y="upload_speed:Q")
    .properties(height=CHART_HEIGHT, width=CHART_WIDTH / 3 - 50)
)

col3.altair_chart(
    alt.Chart(dat, title="Ping by Hour (ms)")
    .mark_boxplot(extent="min-max")
    .encode(x="hour:O", y="ping:Q")
    .properties(height=CHART_HEIGHT, width=CHART_WIDTH / 3 - 50)
)


st.subheader("Ping (ms)")
st.altair_chart(timeseries_chart("ping"))

st.subheader("Upload Speed (Mb/s)")
st.altair_chart(timeseries_chart("upload_speed"))

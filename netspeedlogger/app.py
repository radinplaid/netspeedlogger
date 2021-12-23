import datetime

import altair as alt
import pandas as pd
import streamlit as st

from netspeedlogger.netspeedlogger import selectall_with_date_range, timeseries_chart

st.set_page_config(layout="wide")
st.title("Internet Speed Test Results")

CHART_WIDTH = 1600
CHART_HEIGHT = 400

min_date = datetime.date.today() - datetime.timedelta(days=7)
max_date = datetime.date.today() + datetime.timedelta(days=1)

a_date = st.date_input("Pick a date", (min_date, max_date))


dat = selectall_with_date_range(min_date=str(a_date[0]), max_date=str(a_date[1]))

if not dat:
    st.markdown("No data - run `netspeedlogger run` first!")
else:
    dat["download_speed"] = dat["download_speed"] / (1024 * 1024)
    dat["upload_speed"] = dat["upload_speed"] / (1024 * 1024)
    dat["hour"] = [int(i[11:13]) for i in dat["timestamp"]]

    st.subheader("Download Speed (Mb/s)")
    st.altair_chart(timeseries_chart(dat, "download_speed", CHART_HEIGHT, CHART_WIDTH))

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
    st.altair_chart(timeseries_chart(dat, "ping", CHART_HEIGHT, CHART_WIDTH))

    st.subheader("Upload Speed (Mb/s)")
    st.altair_chart(timeseries_chart(dat, "upload_speed", CHART_HEIGHT, CHART_WIDTH))

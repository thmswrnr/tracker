import datetime
import sqlite3

import streamlit as st
import yaml

from data import Record, generate_db_handler
from tracker import RepMaxTracker, Tracker

st.set_page_config(
    page_title="Tracker",
    page_icon="https://www.google.com/s2/favicons?domain=www.crossfit.com",
    layout="wide",
)

# ========== DATA ==========
LAST_FETCH_ID = 0
NEW_FETCH_ID = 1


@st.experimental_singleton
def get_db():
    db = generate_db_handler("data")
    db.create_tables()
    return db


@st.cache(
    allow_output_mutation=True,
    show_spinner=True,
    max_entries=1,
    hash_funcs={sqlite3.Connection: id, sqlite3.Cursor: id},
)
def fetch_data(db, fetch_id):
    global LAST_FETCH_ID, NEW_FETCH_ID

    LAST_FETCH_ID = fetch_id
    NEW_FETCH_ID = fetch_id + 1

    records = db.get_records()
    activities = db.get_activities()

    return records, activities


@st.cache(allow_output_mutation=True, show_spinner=True)
def fetch_tracker():
    with open("tracker_base.yml", "r") as f:
        base = yaml.safe_load(f)
    with open("tracker_impl.yml", "r") as f:
        impl = yaml.safe_load(f)

    return base, impl


db = get_db()
records, activities = fetch_data(db, LAST_FETCH_ID)

if len(activities) == 0:
    db.add_activity("Clean", "Clean")
    db.add_activity("Snatch", "Snatch")
    db.add_activity("Deadlift", "Deadlift")

    # to force a re-cache, change LAST_FETCH_ID
    records, activities = fetch_data(db, NEW_FETCH_ID)


# ========== ADD RECORD ==========
with st.sidebar.form("add_activity", clear_on_submit=True):
    st.write("Add Activitiy")
    activity = st.selectbox("Activity", activities["activity"], key="act0")

    # date = st.sidebar.date_input("Date", datetime.datetime.now())
    # date = datetime.datetime(date.year, date.month, date.day, 12, 0, 0)
    date = datetime.datetime.now()

    reps = int(st.number_input("Reps/Rounds", min_value=0, max_value=100))
    weight = float(st.number_input("Weight", min_value=0.0, max_value=200.0))
    distance = float(st.number_input("Distance", min_value=0, max_value=10000))
    time = st.time_input("Time", value=datetime.time(0, 0, 0))

    add_record = st.form_submit_button("Add")

    if add_record:
        record = Record(date, activity, reps, weight, distance, time)
        db.add_record(record)
        records, activities = fetch_data(db, NEW_FETCH_ID)


# ========== ADD ACTIVITY ==========
with st.sidebar.expander("Add Activity"):
    activity = st.text_input("Name", key="act_name", max_chars=50)
    act_type = st.text_input("Type", key="act_type", max_chars=50)

    add_activity = st.button("Add", key="add1")

    if add_activity:
        db.add_activity(activity, act_type)
        records, activities = fetch_data(db, NEW_FETCH_ID)


# ========== ADD TRACKER ==========
with st.sidebar.expander("Add Tracker"):
    tracker_base, tracker_impl = fetch_tracker()
    name = st.text_input("Name", key="tracker_name", max_chars=50)
    activity = st.selectbox("Activity", activities["activity"], key="act1")
    tracker = st.selectbox("Tracker", tracker_base.keys())


# ========== STATS ==========
stats = f"""
    Records: {len(records)}\n
    Activities: {len(activities)}\n
    Tracker: TBA\n
    Last record: TBA\n
    Most records: TBA
"""
st.sidebar.info(stats)


# ========== DASHBOARD ==========
st.header("Overview")

act_type_sel = st.multiselect("Activity Type", sorted(activities["type"].unique()))
act_sel = st.multiselect("Activity", sorted(activities["activity"].unique()))

act_by_type = activities[activities["type"].isin(act_type_sel)]["activity"]
act_sel.extend(act_by_type)
act_sel = sorted(list(set(act_sel)))

# only expand when there is only one element
expand = len(act_sel) == 1

if len(act_sel) > 0:
    for act in act_sel:
        with st.expander(act, expanded=expand):
            tracker = {k: v for (k, v) in tracker_impl.items() if v["activity"] == act}

            if len(tracker) == 0:
                st.info("Add a tracker to see something here.")
            else:
                for k, v in tracker.items():
                    t = RepMaxTracker(k, v)
                    t.compute(records[records["activity"] == act])
                    t.render_frame()

    raw_data_sel = act_sel
else:
    raw_data_sel = activities["activity"]

st.header("Raw Data")

with st.expander("Records"):
    st.write(records[records["activity"].isin(raw_data_sel)])

with st.expander("Activities"):
    st.write(activities[activities["activity"].isin(raw_data_sel)])

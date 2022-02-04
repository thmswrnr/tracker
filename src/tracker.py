import re

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from loguru import logger


class Tracker(object):
    def __init__(self, name, desc):
        self.computed = desc["computed"]
        self.plot = desc["plot"]
        self.name = name

        logger.info(f"Initialzed new tracker '{name}'")
        logger.debug(desc)

    def set_data(self, data):
        self.data = data.copy()

        for k, v in self.computed.items():
            compute_str = re.sub(r"\$(.+?)\$", r"self.data['\1']", v)
            self.data[k] = eval(compute_str)

    def generate_plot_mpl(self):
        fig, ax = plt.subplots()
        self.data.plot(x=self.plot["x"], y=self.plot["y"], ax=ax)
        return fig

    @st.cache
    def generate_plot_px(self):
        fig = px.line(
            self.data,
            x=self.plot["x"],
            y=self.plot["y"],
            title=self.name,
            markers=self.plot["markers"],
            labels=self.plot["labels"],
        )

        return fig

    def generate_table(self):
        pass


class RepMaxTracker(object):
    def __init__(self, name, params):
        self.name = name
        self.params = params
        self.data = None

    def compute(self, data):
        # compute values
        # sort by date ascending
        # group by day (max, min, mean)
        df = data.copy()

        df["1RM_BRZYCKI"] = df["weight"] / (1.0278 - (0.0278 * df["reps"]))
        df["1RM_EPLEY"] = (0.033 * df["weight"] * df["reps"]) + df["weight"]
        df["1RM"] = (df["1RM_BRZYCKI"] + df["1RM_EPLEY"]) / 2.0
        df["3RM"] = 0.91 * df["1RM"]
        df["5RM"] = 0.86 * df["1RM"]

        self.data = df

    def render_frame(self):
        if self.data is None:
            st.error("No data provided!")
            return

        fig = px.line(
            self.data,
            x="date",
            y=["1RM", "3RM", "5RM"],
            title=self.name,
            markers=True,
            labels={"date": "Datum", "value": "kg", "variable": "Max. Reps."},
        )

        st.plotly_chart(fig)

        p = st.number_input(
            "Scaling (%)", min_value=10, max_value=200, value=100, step=1
        )

        rm = self.data[["1RM", "3RM", "5RM"]].iloc[-1]

        st.write(f"{p}% von 1RM sind {p*rm['1RM']/100:.1f} kg")
        st.write(f"{p}% von 3RM sind {p*rm['3RM']/100:.1f} kg")
        st.write(f"{p}% von 5RM sind {p*rm['5RM']/100:.1f} kg")

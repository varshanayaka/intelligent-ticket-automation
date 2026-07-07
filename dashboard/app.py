"""
Reporting dashboard -- the "automated service management and reporting"
piece from the JD. Run with: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
import plotly.express as px
from src.db import get_connection

st.set_page_config(page_title="IT Ticket Automation Dashboard", layout="wide")


@st.cache_data(ttl=30)
def load_data():
    with get_connection() as conn:
        tickets = pd.read_sql_query("SELECT * FROM tickets", conn)
        monitoring = pd.read_sql_query("SELECT * FROM monitoring_events", conn)
        bot_runs = pd.read_sql_query("SELECT * FROM bot_runs", conn)
    tickets["created_at"] = pd.to_datetime(tickets["created_at"])
    tickets["date"] = tickets["created_at"].dt.date
    return tickets, monitoring, bot_runs


tickets, monitoring, bot_runs = load_data()

st.title("🤖 Intelligent IT Ticket Automation — Ops Dashboard")
st.caption("Simulated Application Maintenance queue with automated classification, "
           "resolution bots, self-healing monitoring, and reporting.")

# ---- Top KPI row ----
total = len(tickets)
auto_resolved = (tickets["status"] == "auto_resolved").sum()
escalated = (tickets["status"] == "escalated").sum()
automation_rate = (auto_resolved / total * 100) if total else 0
avg_mttr = tickets.loc[tickets["mttr_minutes"].notna(), "mttr_minutes"].mean()
self_healed = (monitoring["action_taken"] == "self_healed").sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Tickets", f"{total}")
col2.metric("Automation Rate", f"{automation_rate:.1f}%")
col3.metric("Auto-Resolved", f"{auto_resolved}")
col4.metric("Avg MTTR (min)", f"{avg_mttr:.1f}" if pd.notna(avg_mttr) else "—")
col5.metric("Self-Healed (pre-ticket)", f"{self_healed}")

st.divider()

# ---- Charts row ----
c1, c2 = st.columns(2)

with c1:
    st.subheader("Ticket Volume Over Time")
    daily = tickets.groupby("date").size().reset_index(name="count")
    fig = px.bar(daily, x="date", y="count", labels={"count": "Tickets"})
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Resolution Outcome")
    status_counts = tickets["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig = px.pie(status_counts, names="status", values="count", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    st.subheader("Tickets by Category")
    cat_counts = tickets["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(cat_counts, x="count", y="category", orientation="h")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Bot Performance")
    if not bot_runs.empty:
        bot_perf = bot_runs.groupby(["bot_name", "outcome"]).size().reset_index(name="count")
        fig = px.bar(bot_perf, x="bot_name", y="count", color="outcome", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No bot runs yet -- run `python src/main.py` first.")

st.divider()
st.subheader("Recent Tickets")
st.dataframe(
    tickets.sort_values("created_at", ascending=False)
           [["ticket_id", "created_at", "category", "severity", "status",
             "resolved_by", "mttr_minutes"]]
           .head(25),
    use_container_width=True,
)

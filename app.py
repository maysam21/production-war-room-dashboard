import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import load_data

st.set_page_config(page_title="Production War Room",
                   layout="wide")

st.title("🏭 Production War-Room Dashboard")

# File Upload (Cloud Safe)
uploaded_file = st.sidebar.file_uploader(
    "Upload Production Excel File",
    type=["xlsx"]
)

if uploaded_file is not None:

    df, weekly_df = load_data(uploaded_file)

    selected_week = st.sidebar.selectbox(
        "Select Week",
        weekly_df["Week"]
    )

    row = weekly_df[weekly_df["Week"] == selected_week].iloc[0]

    target = row["Target"]
    achieved = row["Achieved"]
    variance = achieved - target
    percent = (achieved / target) * 100 if target > 0 else 0

    # RAG
    if percent < 90:
        rag_status = "🔴 RED"
    elif percent <= 100:
        rag_status = "🟡 AMBER"
    else:
        rag_status = "🟢 GREEN"

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Target", int(target))
    col2.metric("Achieved", int(achieved))
    col3.metric("Achievement %", f"{percent:.1f}%")
    col4.metric("Variance", int(variance))
    col5.markdown(f"### {rag_status}")

    st.divider()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weekly_df["Week"],
        y=weekly_df["Target"],
        mode="lines+markers",
        name="Target"
    ))
    fig.add_trace(go.Scatter(
        x=weekly_df["Week"],
        y=weekly_df["Achieved"],
        mode="lines+markers",
        name="Achieved"
    ))

    fig.update_layout(title="Weekly Target vs Achieved Trend")

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload your Production Plan Excel file to begin.")

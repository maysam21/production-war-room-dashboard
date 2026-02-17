import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="S&OP Dashboard", layout="wide")

st.title("📊 S&OP Executive Dashboard")

uploaded_file = st.sidebar.file_uploader(
    "Upload Production Plan Excel",
    type=["xlsx"]
)

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file, sheet_name="S&OP")

    # Keep only relevant columns
    df = df[["Model", "Category", "OND", "Oct", "Nov", "Dec"]]

    month = st.sidebar.selectbox(
        "Select Month",
        ["Oct", "Nov", "Dec"]
    )

    # Filter active models
    df_month = df[df[month] > 0]

    total_plan = df_month[month].sum()

    chimney_plan = df_month[df_month["Category"] == "Chimney"][month].sum()
    hob_plan = df_month[df_month["Category"] == "Hob"][month].sum()
    cooktop_plan = df_month[df_month["Category"] == "Cooktop"][month].sum()

    model_count = df_month["Model"].nunique()

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Plan", int(total_plan))
    col2.metric("Chimney", int(chimney_plan))
    col3.metric("Hob", int(hob_plan))
    col4.metric("Cooktop", int(cooktop_plan))
    col5.metric("Active Models", model_count)

    st.divider()

    # Category Chart
    category_summary = df_month.groupby("Category")[month].sum().reset_index()

    fig = go.Figure()
    fig.add_bar(x=category_summary["Category"],
                y=category_summary[month])

    fig.update_layout(title=f"{month} Category-wise Plan")

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Model-wise Table
    st.subheader(f"{month} Model-wise Plan")

    st.dataframe(df_month[["Model", "Category", month]].sort_values(by=month, ascending=False))

    st.divider()

    # Quarter OND View
    if st.checkbox("Show OND Quarter View"):

        total_ond = df["OND"].sum()

        fig_q = go.Figure()
        fig_q.add_bar(x=df["Model"],
                      y=df["OND"])

        fig_q.update_layout(title="OND Quarter Plan (Model-wise)")

        st.metric("Total OND Plan", int(total_ond))
        st.plotly_chart(fig_q, use_container_width=True)

else:
    st.info("Upload Excel file to start S&OP Dashboard.")

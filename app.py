import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Quarter Production Plan", layout="wide")

st.title("🏭 Quarterly Production Plan Dashboard")

uploaded_file = st.sidebar.file_uploader(
    "Upload Production Plan Excel",
    type=["xlsx"]
)

if uploaded_file is not None:

    df = pd.read_excel(uploaded_file, sheet_name="S&OP")

    # Remove completely empty rows
    df = df.dropna(how="all")

    # Detect quarter column dynamically
    quarter_list = ["OND", "JFM", "AMJ", "JAS"]
    detected_quarter = None

    for q in quarter_list:
        if q in df.columns:
            detected_quarter = q

    # Since quarters are stacked vertically,
    # detect which rows belong to which quarter
    quarter_sections = {}
    current_quarter = None

    for index, row in df.iterrows():
        for q in quarter_list:
            if q in row.values:
                current_quarter = q
                quarter_sections[current_quarter] = []
        if current_quarter:
            quarter_sections[current_quarter].append(row)

    # Convert sections to dataframe
    clean_data = {}
    for q, rows in quarter_sections.items():
        temp_df = pd.DataFrame(rows)
        temp_df = temp_df.dropna(how="all")
        clean_data[q] = temp_df

    if not clean_data:
        st.error("Quarter structure not detected correctly.")
        st.stop()

    selected_quarter = st.sidebar.selectbox(
        "Select Quarter",
        list(clean_data.keys())
    )

    df_q = clean_data[selected_quarter]

    # Identify month mapping
    month_map = {
        "OND": ["Oct", "Nov", "Dec"],
        "JFM": ["Jan", "Feb", "Mar"],
        "AMJ": ["Apr", "May", "Jun"],
        "JAS": ["Jul", "Aug", "Sep"]
    }

    months = month_map[selected_quarter]

    # Keep relevant columns only
    df_q = df_q[["Model", "Category", selected_quarter] + months]

    df_q = df_q.fillna(0)

    # ---------------------
    # Quarter Summary
    # ---------------------

    total_quarter = df_q[selected_quarter].sum()

    category_summary = df_q.groupby("Category")[selected_quarter].sum().reset_index()

    st.subheader(f"📊 {selected_quarter} Quarter Summary")

    col1, col2 = st.columns(2)
    col1.metric("Total Quarter Plan", int(total_quarter))
    col2.dataframe(category_summary)

    st.divider()

    # ---------------------
    # Month-wise Plan
    # ---------------------

    month_totals = {m: df_q[m].sum() for m in months}

    fig = go.Figure()
    fig.add_bar(x=list(month_totals.keys()),
                y=list(month_totals.values()))

    fig.update_layout(title=f"{selected_quarter} Month-wise Production Plan")

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ---------------------
    # SKU-wise Plan
    # ---------------------

    st.subheader("📦 SKU-wise Production Plan")

    st.dataframe(
        df_q.sort_values(by=selected_quarter, ascending=False),
        use_container_width=True
    )

else:
    st.info("Upload Excel file to generate Quarterly Production Plan.")

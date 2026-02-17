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

    df_raw = pd.read_excel(uploaded_file, sheet_name="S&OP", header=None)

    quarter_names = ["OND", "JFM", "AMJ", "JAS"]
    quarter_data = {}

    i = 0
    while i < len(df_raw):

        row_values = df_raw.iloc[i].astype(str).tolist()

        for q in quarter_names:
            if q in row_values:

                header = df_raw.iloc[i].tolist()
                header = [str(h).strip() for h in header]

                data_rows = []
                j = i + 1

                while j < len(df_raw):

                    row_check = str(df_raw.iloc[j][1]).strip().upper()

                    if row_check == "TOTAL":
                        break

                    data_rows.append(df_raw.iloc[j].tolist())
                    j += 1

                df_q = pd.DataFrame(data_rows, columns=header)

                # Remove empty rows
                df_q = df_q.dropna(how="all")

                # Remove duplicate columns
                df_q = df_q.loc[:, ~df_q.columns.duplicated()]

                quarter_data[q] = df_q
                i = j
                break

        i += 1

    if not quarter_data:
        st.error("Quarter blocks not detected properly.")
        st.stop()

    selected_quarter = st.sidebar.selectbox(
        "Select Quarter",
        list(quarter_data.keys())
    )

    df_q = quarter_data[selected_quarter].copy()

    # Clean column names
    df_q.columns = [str(c).strip() for c in df_q.columns]

    # Identify months correctly
    month_map = {
        "OND": ["Oct", "Nov", "Dec"],
        "JFM": ["Jan", "Feb", "Mar"],
        "AMJ": ["April", "May", "June"],
        "JAS": ["Jul", "Aug", "Sep"]
    }

    months = month_map.get(selected_quarter, [])

    # Convert only relevant numeric columns safely
    numeric_cols = [selected_quarter] + months

    for col in numeric_cols:
        if col in df_q.columns:
            df_q[col] = pd.to_numeric(df_q[col], errors="coerce").fillna(0)

    # -------------------------
    # Quarter Summary
    # -------------------------

    total_quarter = df_q[selected_quarter].sum()

    category_summary = (
        df_q.groupby("Category")[selected_quarter]
        .sum()
        .reset_index()
    )

    st.subheader(f"📊 {selected_quarter} Quarter Summary")

    col1, col2 = st.columns(2)
    col1.metric("Total Quarter Plan", int(total_quarter))
    col2.dataframe(category_summary)

    st.divider()

    # -------------------------
    # Month-wise Plan
    # -------------------------

    month_totals = {}

    for m in months:
        if m in df_q.columns:
            month_totals[m] = df_q[m].sum()

    fig = go.Figure()
    fig.add_bar(
        x=list(month_totals.keys()),
        y=list(month_totals.values())
    )

    fig.update_layout(title=f"{selected_quarter} Month-wise Production Plan")

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -------------------------
    # SKU-wise Plan
    # -------------------------

    st.subheader("📦 SKU-wise Production Plan")

    st.dataframe(
        df_q.sort_values(by=selected_quarter, ascending=False),
        use_container_width=True
    )

else:
    st.info("Upload Excel file to generate Quarterly Production Plan.")

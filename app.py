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

    # Read raw sheet (no header)
    df_raw = pd.read_excel(uploaded_file, sheet_name="S&OP", header=None)

    quarter_names = ["OND", "JFM", "AMJ", "JAS"]
    quarter_data = {}

    i = 0
    while i < len(df_raw):

        row = df_raw.iloc[i].astype(str).tolist()

        # Detect header row containing quarter name
        for q in quarter_names:
            if q in row:

                # This is header row
                header_row = df_raw.iloc[i]
                columns = header_row.tolist()

                # Data starts from next row
                data_start = i + 1
                data_rows = []

                j = data_start
                while j < len(df_raw):

                    current_row = df_raw.iloc[j]

                    # Stop at TOTAL row
                    if str(current_row[1]).strip().upper() == "TOTAL":
                        break

                    data_rows.append(current_row.tolist())
                    j += 1

                # Create DataFrame for this quarter
                df_q = pd.DataFrame(data_rows, columns=columns)

                # Remove completely empty rows
                df_q = df_q.dropna(how="all")

                quarter_data[q] = df_q

                i = j  # Move pointer
                break

        i += 1

    if not quarter_data:
        st.error("Quarter blocks not detected.")
        st.stop()

    selected_quarter = st.sidebar.selectbox(
        "Select Quarter",
        list(quarter_data.keys())
    )

    df_q = quarter_data[selected_quarter].copy()

    # Clean numeric columns
    for col in df_q.columns:
        df_q[col] = pd.to_numeric(df_q[col], errors="ignore")

    # Identify month columns dynamically
    month_map = {
        "OND": ["Oct", "Nov", "Dec"],
        "JFM": ["Jan", "Feb", "Mar"],
        "AMJ": ["April", "May", "June"],
        "JAS": ["Jul", "Aug", "Sep"]
    }

    months = month_map[selected_quarter]

    # ---------------------
    # Quarter Summary
    # ---------------------

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

    # ---------------------
    # Month-wise Plan
    # ---------------------

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

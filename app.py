import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Production Planning Dashboard", layout="wide")

st.title("🏭 Production Planning Dashboard")

uploaded_file = st.sidebar.file_uploader(
    "Upload Production Plan Excel",
    type=["xlsx"]
)

# =========================================================
# 🔹 Global Month Map
# =========================================================
month_map = {
    "OND": ["Oct", "Nov", "Dec"],
    "JFM": ["Jan", "Feb", "Mar"],
    "AMJ": ["April", "May", "June"],
    "JAS": ["Jul", "Aug", "Sep"]
}

if uploaded_file is not None:

    df_raw = pd.read_excel(uploaded_file, sheet_name="S&OP", header=None)

    quarter_names = ["OND", "JFM", "AMJ", "JAS"]
    quarter_data = {}

    # =========================================================
    # 🔹 Robust Quarter Block Parser
    # =========================================================
    for i in range(len(df_raw)):

        row = df_raw.iloc[i].astype(str).str.strip().tolist()

        for q in quarter_names:

            if (
                "Sl. No" in row and
                "Model" in row and
                "Category" in row and
                q in row
            ):

                header = df_raw.iloc[i].tolist()
                header = [str(h).strip() for h in header]

                data_rows = []
                j = i + 1

                while j < len(df_raw):

                    sl_value = df_raw.iloc[j][0]

                    if pd.isna(sl_value):
                        break

                    try:
                        int(sl_value)
                    except:
                        break

                    data_rows.append(df_raw.iloc[j].tolist())
                    j += 1

                df_q = pd.DataFrame(data_rows, columns=header)

                if "Sl. No" in df_q.columns:
                    df_q = df_q.drop(columns=["Sl. No"])

                df_q.columns = df_q.columns.str.strip()

                required_cols = ["Model", "Category", q] + month_map[q]
                df_q = df_q[required_cols]

                df_q["Category"] = df_q["Category"].astype(str).str.strip()

                for col in [q] + month_map[q]:
                    df_q[col] = pd.to_numeric(df_q[col], errors="coerce").fillna(0)

                quarter_data[q] = df_q

    if not quarter_data:
        st.error("Quarter blocks not detected properly.")
        st.stop()

    # =========================================================
    # 🔹 Quarter Selection
    # =========================================================
    selected_quarter = st.sidebar.selectbox(
        "Select Quarter",
        list(quarter_data.keys())
    )

    df_q = quarter_data[selected_quarter].copy()
    months = month_map.get(selected_quarter, [])

    if not months:
        st.stop()

    # =========================================================
    # 🔹 Production Plan Section
    # =========================================================
    st.header(f"📊 {selected_quarter} Production Plan")

    total_quarter = df_q[selected_quarter].sum()

    col1, col2 = st.columns(2)

    col1.metric("Total Quarter Plan", int(total_quarter))

    category_summary = (
        df_q.groupby("Category")[selected_quarter]
        .sum()
        .reset_index()
    )

    col2.dataframe(category_summary, use_container_width=True)

    st.divider()

    # Month-wise Chart
    month_totals = {m: df_q[m].sum() for m in months}

    fig = go.Figure()
    fig.add_bar(
        x=list(month_totals.keys()),
        y=list(month_totals.values())
    )

    fig.update_layout(
        title=f"{selected_quarter} Month-wise Production Plan",
        xaxis_title="Month",
        yaxis_title="Quantity"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📦 SKU-wise Production Plan")
    st.dataframe(
        df_q.sort_values(by=selected_quarter, ascending=False),
        use_container_width=True
    )

   # =========================================================
# 🏭 Vendor Capacity Planning (Month-wise + SKU Mapping)
# =========================================================

st.markdown("----")
st.header("🏭 Vendor Capacity Planning (Month-wise)")

selected_month = st.selectbox("Select Month", months)

st.subheader("Add Vendors")

num_vendors = st.number_input(
    "Number of Vendors",
    min_value=1,
    max_value=5,
    value=1
)

vendor_data = []
assignment_data = []

for i in range(num_vendors):

    col1, col2, col3 = st.columns(3)

    name = col1.text_input("Vendor Name", key=f"vname_{i}")
    category = col2.selectbox(
        "Category",
        sorted(df_q["Category"].unique()),
        key=f"vcat_{i}"
    )
    capacity = col3.number_input(
        f"{selected_month} Capacity",
        min_value=0,
        value=0,
        key=f"vcap_{i}"
    )

    if name:

        vendor_data.append({
            "Vendor": name,
            "Category": category,
            "Capacity": capacity
        })

        # Compact SKU Mapping
        with st.expander(f"Map SKUs for {name} ({category})"):

            sku_list = df_q[df_q["Category"] == category]["Model"].tolist()

            selected_skus = st.multiselect(
                "Select SKUs",
                sku_list,
                key=f"sku_map_{i}"
            )

            for sku in selected_skus:

                plan_value = df_q[
                    df_q["Model"] == sku
                ][selected_month].values[0]

                assignment_data.append({
                    "Vendor": name,
                    "Model": sku,
                    "Plan": plan_value
                })

vendor_df = pd.DataFrame(vendor_data)
assignment_df = pd.DataFrame(assignment_data)

st.markdown("----")
st.subheader("Vendor Utilization Summary")

results = []

for _, row in vendor_df.iterrows():

    vendor = row["Vendor"]
    capacity = row["Capacity"]

    vendor_plan = assignment_df[
        assignment_df["Vendor"] == vendor
    ]["Plan"].sum()

    utilization = (vendor_plan / capacity) * 100 if capacity > 0 else 0
    gap = capacity - vendor_plan

    if utilization > 100:
        status = "🔴 Overloaded"
    elif utilization >= 85:
        status = "🟡 Tight"
    else:
        status = "🟢 Comfortable"

    results.append({
        "Vendor": vendor,
        "Assigned Plan": int(vendor_plan),
        "Capacity": int(capacity),
        "Utilization %": round(utilization, 1),
        "Gap": int(gap),
        "Status": status
    })

result_df = pd.DataFrame(results)

st.dataframe(result_df, use_container_width=True)

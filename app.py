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
    # 🔹 Quarter Block Parser
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
    # 🔹 Separate Tabs
    # =========================================================
    tab1, tab2 = st.tabs(["📊 Production Plan", "🏭 Capacity Planning"])

    # =========================================================
    # TAB 1 - Production Plan
    # =========================================================
    with tab1:

        st.header(f"{selected_quarter} Production Plan")

        total_quarter = df_q[selected_quarter].sum()
        st.metric("Total Quarter Plan", int(total_quarter))

        month_totals = {m: df_q[m].sum() for m in months}

        fig = go.Figure()
        fig.add_bar(
            x=list(month_totals.keys()),
            y=list(month_totals.values())
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Quantity"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("SKU-wise Plan")
        st.dataframe(df_q, use_container_width=True)

    # =========================================================
    # TAB 2 - Clean SKU-wise Capacity Planning
    # =========================================================
    with tab2:

        st.header("🏭 SKU-wise Capacity Planning")

        selected_month = st.selectbox("Select Month", months)

        # ----------------------------
        # Vendor Setup
        # ----------------------------
        st.markdown("### Vendor Setup")

        num_vendors = st.number_input(
            "Number of Vendors",
            min_value=1,
            max_value=5,
            value=1
        )

        vendors = []

        for i in range(num_vendors):

            col1, col2, col3 = st.columns(3)

            name = col1.text_input("Vendor Name", key=f"vname_{i}")
            category = col2.selectbox(
                "Category",
                sorted(df_q["Category"].unique()),
                key=f"vcat_{i}"
            )
            total_capacity = col3.number_input(
                f"{selected_month} Total Capacity",
                min_value=0,
                value=0,
                key=f"vtotalcap_{i}"
            )

            if name:
                vendors.append({
                    "Vendor": name,
                    "Category": category,
                    "Total Capacity": total_capacity
                })

        # ----------------------------
        # SKU Capacity Mapping
        # ----------------------------
        st.markdown("----")
        st.markdown("### SKU Capacity Mapping")

        sku_allocation_records = []

        for vendor in vendors:

            st.markdown(f"#### {vendor['Vendor']} ({vendor['Category']})")

            sku_list = df_q[
                df_q["Category"] == vendor["Category"]
            ]["Model"].tolist()

            selected_skus = st.multiselect(
                "Select SKUs",
                sku_list,
                key=f"sku_select_{vendor['Vendor']}"
            )

            for sku in selected_skus:

                sku_capacity = st.number_input(
                    f"{sku} Capacity for {vendor['Vendor']}",
                    min_value=0,
                    value=0,
                    key=f"{vendor['Vendor']}_{sku}"
                )

                sku_allocation_records.append({
                    "Vendor": vendor["Vendor"],
                    "SKU": sku,
                    "SKU Capacity": sku_capacity
                })

            st.markdown("----")

        allocation_df = pd.DataFrame(sku_allocation_records)

        # ----------------------------
        # Allocation Engine
        # ----------------------------
        st.subheader("Vendor Utilization Summary")

        vendor_results = []

        for vendor in vendors:

            vendor_name = vendor["Vendor"]
            vendor_total_capacity = vendor["Total Capacity"]

            vendor_sku_df = allocation_df[
                allocation_df["Vendor"] == vendor_name
            ]

            vendor_allocated_total = 0

            for _, sku_row in vendor_sku_df.iterrows():

                sku = sku_row["SKU"]
                sku_capacity_limit = sku_row["SKU Capacity"]

                sku_plan = df_q[
                    df_q["Model"] == sku
                ][selected_month].values[0]

                allocated = min(sku_plan, sku_capacity_limit)

                vendor_allocated_total += allocated

            utilization = (
                vendor_allocated_total / vendor_total_capacity * 100
                if vendor_total_capacity > 0 else 0
            )

            gap = vendor_total_capacity - vendor_allocated_total

            if utilization > 100:
                status = "🔴 Overloaded"
            elif utilization >= 85:
                status = "🟡 Tight"
            else:
                status = "🟢 Comfortable"

            vendor_results.append({
                "Vendor": vendor_name,
                "Allocated Plan": int(vendor_allocated_total),
                "Total Capacity": int(vendor_total_capacity),
                "Utilization %": round(utilization, 1),
                "Gap": int(gap),
                "Status": status
            })

        vendor_result_df = pd.DataFrame(vendor_results)

        st.dataframe(vendor_result_df, use_container_width=True)

else:
    st.info("Upload Excel file to start.")

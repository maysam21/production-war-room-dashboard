import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Production Control Tower", layout="wide")

st.title("🏭 Production Control Tower")

uploaded_file = st.sidebar.file_uploader(
    "Upload Production Plan Excel",
    type=["xlsx"]
)

# =========================================================
# Month Map
# =========================================================
month_map = {
    "OND": ["Oct", "Nov", "Dec"],
    "JFM": ["Jan", "Feb", "Mar"],
    "AMJ": ["April", "May", "June"],
    "JAS": ["Jul", "Aug", "Sep"]
}

if uploaded_file is not None:

    # =========================================================
    # READ S&OP SHEET
    # =========================================================
    df_raw = pd.read_excel(uploaded_file, sheet_name="S&OP", header=None)

    quarter_names = ["OND", "JFM", "AMJ", "JAS"]
    quarter_data = {}

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
    # READ COGS - Temp SHEET
    # =========================================================
    try:
        cogs_master = pd.read_excel(uploaded_file, sheet_name="COGS - Temp")
        cogs_master.columns = cogs_master.columns.str.strip()

        # Rename Product → Model for merge
        if "Product" not in cogs_master.columns:
            st.error("Column 'Product' not found in COGS - Temp sheet.")
            st.stop()

        cogs_master = cogs_master.rename(columns={"Product": "Model"})

        # Only take required columns
        required_cols = ["Model", "Material Cost",
                         "Conversion Cost", "Selling Price"]

        for col in required_cols:
            if col not in cogs_master.columns:
                cogs_master[col] = 0

        cogs_master = cogs_master[required_cols].fillna(0)

    except:
        st.warning("COGS - Temp sheet not found.")
        cogs_master = pd.DataFrame()

    # =========================================================
    # Quarter Selection
    # =========================================================
    selected_quarter = st.sidebar.selectbox(
        "Select Quarter",
        list(quarter_data.keys())
    )

    df_q = quarter_data[selected_quarter].copy()
    months = month_map[selected_quarter]

    # =========================================================
    # Tabs
    # =========================================================
    tab1, tab2, tab3 = st.tabs(
        ["📊 Production Plan", "🏭 Capacity Planning", "💰 COGS & GM Analysis"]
    )

    # =========================================================
    # TAB 1 - Production
    # =========================================================
    with tab1:

        st.header(f"{selected_quarter} Production Plan")

        total_plan = df_q[selected_quarter].sum()
        st.metric("Total Quarter Plan", int(total_plan))

        month_totals = {m: df_q[m].sum() for m in months}

        fig = go.Figure()
        fig.add_bar(x=list(month_totals.keys()),
                    y=list(month_totals.values()))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_q, use_container_width=True)

    # =========================================================
    # TAB 2 - Capacity
    # =========================================================
    with tab2:

        st.header("🏭 Capacity Planning")

        selected_month = st.selectbox("Select Month", months)

        num_vendors = st.number_input("Number of Vendors", 1, 5, 1)

        vendor_results = []

        for i in range(num_vendors):

            col1, col2, col3 = st.columns(3)

            name = col1.text_input("Vendor Name", key=f"vname_{i}")
            category = col2.selectbox(
                "Category",
                sorted(df_q["Category"].unique()),
                key=f"vcat_{i}"
            )
            capacity = col3.number_input(
                "Monthly Capacity",
                min_value=0,
                value=0,
                key=f"vcap_{i}"
            )

            if name:

                category_plan = df_q[
                    df_q["Category"] == category
                ][selected_month].sum()

                utilization = (
                    category_plan / capacity * 100
                    if capacity > 0 else 0
                )

                gap = capacity - category_plan

                vendor_results.append({
                    "Vendor": name,
                    "Category": category,
                    "Plan": int(category_plan),
                    "Capacity": int(capacity),
                    "Utilization %": round(utilization, 1),
                    "Gap": int(gap)
                })

        if vendor_results:
            st.dataframe(pd.DataFrame(vendor_results),
                         use_container_width=True)

    # =========================================================
    # TAB 3 - COGS & GM%
    # =========================================================
    with tab3:

        st.header("💰 COGS & Gross Margin Analysis")

        if cogs_master.empty:
            st.warning("COGS - Temp sheet missing.")
            st.stop()

        selected_month = st.selectbox(
            "Select Month for Financial Analysis",
            months,
            key="finance_month"
        )

        merged = df_q.merge(
            cogs_master,
            how="left",
            on="Model"
        ).fillna(0)

        merged["Plan Qty"] = merged[selected_month]

        merged["Total Unit Cost"] = (
            merged["Material Cost"] +
            merged["Conversion Cost"]
        )

        merged["Total COGS"] = (
            merged["Plan Qty"] *
            merged["Total Unit Cost"]
        )

        merged["Revenue"] = (
            merged["Plan Qty"] *
            merged["Selling Price"]
        )

        merged["Gross Profit"] = (
            merged["Revenue"] -
            merged["Total COGS"]
        )

        merged["GM %"] = (
            merged["Gross Profit"] /
            merged["Revenue"] * 100
        ).replace([float("inf"), -float("inf")], 0).fillna(0)

        finance_df = merged[
            ["Model", "Category", "Plan Qty",
             "Total Unit Cost", "Total COGS",
             "Revenue", "Gross Profit", "GM %"]
        ]

        st.subheader("SKU Financial Summary")
        st.dataframe(finance_df, use_container_width=True)

        # ================= Summary =================
        total_revenue = finance_df["Revenue"].sum()
        total_cogs = finance_df["Total COGS"].sum()
        total_gp = finance_df["Gross Profit"].sum()

        overall_gm = (
            total_gp / total_revenue * 100
            if total_revenue > 0 else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Revenue", f"{total_revenue:,.0f}")
        col2.metric("Total COGS", f"{total_cogs:,.0f}")
        col3.metric("Gross Profit", f"{total_gp:,.0f}")
        col4.metric("Overall GM %", f"{overall_gm:.2f}%")

        # Category Summary
        st.subheader("Category Profitability")

        category_summary = (
            finance_df.groupby("Category")
            .agg({
                "Revenue": "sum",
                "Total COGS": "sum",
                "Gross Profit": "sum"
            })
            .reset_index()
        )

        category_summary["GM %"] = (
            category_summary["Gross Profit"] /
            category_summary["Revenue"] * 100
        ).replace([float("inf"), -float("inf")], 0).fillna(0)

        st.dataframe(category_summary, use_container_width=True)

        fig = go.Figure()
        fig.add_bar(
            x=category_summary["Category"],
            y=category_summary["GM %"]
        )
        fig.update_layout(title="Category GM %")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload Excel file to start.")

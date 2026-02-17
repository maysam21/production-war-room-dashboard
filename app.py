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

    month_map = {
        "OND": ["Oct", "Nov", "Dec"],
        "JFM": ["Jan", "Feb", "Mar"],
        "AMJ": ["April", "May", "June"],
        "JAS": ["Jul", "Aug", "Sep"]
    }

    quarter_data = {}

    # -----------------------------
    # Robust Quarter Block Parser
    # -----------------------------
    for i in range(len(df_raw)):

        row = df_raw.iloc[i].astype(str).str.strip().tolist()

        for q in quarter_names:

            # Detect real header row
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

                    # Stop when Sl. No not numeric
                    if pd.isna(sl_value):
                        break

                    try:
                        int(sl_value)
                    except:
                        break

                    data_rows.append(df_raw.iloc[j].tolist())
                    j += 1

                df_q = pd.DataFrame(data_rows, columns=header)

                # Remove Sl. No column safely
                if "Sl. No" in df_q.columns:
                    df_q = df_q.drop(columns=["Sl. No"])

                # Clean column names
                df_q.columns = df_q.columns.str.strip()

                # Keep only required columns
                required_cols = ["Model", "Category", q] + month_map[q]
                df_q = df_q[required_cols]

                # Clean Category values (remove extra spaces)
                df_q["Category"] = df_q["Category"].astype(str).str.strip()

                # Convert numeric columns safely
                for col in [q] + month_map[q]:
                    df_q[col] = pd.to_numeric(df_q[col], errors="coerce").fillna(0)

                quarter_data[q] = df_q

    if not quarter_data:
        st.error("Quarter blocks not detected properly.")
        st.stop()

    # -----------------------------
    # Sidebar Filters
    # -----------------------------

    selected_quarter = st.sidebar.selectbox(
        "Select Quarter",
        list(quarter_data.keys())
    )

    df_q = quarter_data[selected_quarter].copy()

    # Clean category list
    category_list = sorted(df_q["Category"].dropna().unique().tolist())
    category_options = ["All"] + category_list

    selected_category = st.sidebar.selectbox(
        "Select Category",
        category_options
    )

    if selected_category != "All":
        df_q = df_q[df_q["Category"] == selected_category]

    months = month_map[selected_quarter]

    # -----------------------------
    # Quarter Summary
    # -----------------------------

    total_quarter = df_q[selected_quarter].sum()

    st.subheader(f"📊 {selected_quarter} Quarter Summary")

    col1, col2 = st.columns(2)

    col1.metric("Total Quarter Plan", int(total_quarter))

    category_summary = (
        df_q.groupby("Category")[selected_quarter]
        .sum()
        .reset_index()
    )

    col2.dataframe(category_summary, use_container_width=True)

    st.divider()

    # -----------------------------
    # Month-wise Plan Chart
    # -----------------------------

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

    # -----------------------------
    # SKU-wise Table
    # -----------------------------

    st.subheader("📦 SKU-wise Production Plan")

    st.dataframe(
        df_q.sort_values(by=selected_quarter, ascending=False),
        use_container_width=True
    )

else:
    st.info("Upload Excel file to generate Quarterly Production Plan.")
    # =========================================================
# 🏭 Vendor Capacity Planning Section
# =========================================================

st.markdown("----")
st.header("🏭 Vendor Capacity Planning")

# -----------------------------
# Vendor Capacity Input
# -----------------------------

st.subheader("Vendor Capacity Input")

vendor_data = []

num_vendors = st.number_input(
    "Number of Vendors",
    min_value=1,
    max_value=10,
    value=1
)

for i in range(num_vendors):

    st.markdown(f"### Vendor {i+1}")

    col1, col2, col3 = st.columns(3)

    vendor_name = col1.text_input(f"Vendor Name {i+1}", key=f"name_{i}")
    vendor_category = col2.selectbox(
        f"Category {i+1}",
        sorted(df_q["Category"].unique()),
        key=f"cat_{i}"
    )
    vendor_capacity = col3.number_input(
        f"{selected_quarter} Capacity {i+1}",
        min_value=0,
        value=0,
        key=f"cap_{i}"
    )

    vendor_data.append({
        "Vendor": vendor_name,
        "Category": vendor_category,
        "Capacity": vendor_capacity
    })

vendor_df = pd.DataFrame(vendor_data)

st.markdown("----")

# -----------------------------
# Capacity vs Plan Comparison
# -----------------------------

# =========================================================
# 🏭 Advanced Vendor Capacity Planning
# =========================================================

st.markdown("----")
st.header("🏭 Vendor Capacity Planning")

# ----------------------------------
# Step 1: Vendor Setup
# ----------------------------------

st.subheader("Vendor Setup")

vendor_names = st.text_area(
    "Enter Vendor Names (one per line)",
    "Vendor A\nVendor B"
).split("\n")

vendor_names = [v.strip() for v in vendor_names if v.strip() != ""]

vendor_capacity_dict = {}

for vendor in vendor_names:
    vendor_capacity_dict[vendor] = st.number_input(
        f"{vendor} - {selected_quarter} Capacity",
        min_value=0,
        value=0,
        key=f"cap_{vendor}"
    )

st.markdown("----")

# ----------------------------------
# Step 2: SKU Assignment to Vendors
# ----------------------------------

st.subheader("SKU to Vendor Assignment")

assignment_data = []

for idx, row in df_q.iterrows():

    col1, col2, col3 = st.columns([2,2,2])

    col1.write(row["Model"])
    col2.write(int(row[selected_quarter]))

    assigned_vendor = col3.selectbox(
        f"Assign Vendor for {row['Model']}",
        vendor_names,
        key=f"assign_{idx}"
    )

    assignment_data.append({
        "Model": row["Model"],
        "Vendor": assigned_vendor,
        "Plan": row[selected_quarter]
    })

assignment_df = pd.DataFrame(assignment_data)

st.markdown("----")

# ----------------------------------
# Step 3: Vendor Load Calculation
# ----------------------------------

st.subheader("Vendor Load & Utilization")

capacity_results = []

for vendor in vendor_names:

    vendor_plan = assignment_df[
        assignment_df["Vendor"] == vendor
    ]["Plan"].sum()

    capacity = vendor_capacity_dict[vendor]

    utilization = (vendor_plan / capacity) * 100 if capacity > 0 else 0
    gap = capacity - vendor_plan

    if utilization > 100:
        status = "🔴 Overloaded"
    elif utilization >= 85:
        status = "🟡 Tight"
    else:
        status = "🟢 Comfortable"

    capacity_results.append({
        "Vendor": vendor,
        "Assigned Plan": int(vendor_plan),
        "Capacity": int(capacity),
        "Utilization %": round(utilization, 1),
        "Gap": int(gap),
        "Status": status
    })

capacity_df = pd.DataFrame(capacity_results)

st.dataframe(capacity_df, use_container_width=True)

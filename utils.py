import pandas as pd

def load_data(file_path):

    df_raw = pd.read_excel(file_path, sheet_name="Weekly target Vs achieved", header=None)

    header = df_raw.iloc[0]
    df = df_raw[1:].copy()
    df.columns = header
    df = df.loc[:, df.columns.notna()]
    df.rename(columns={df.columns[0]: "Product"}, inplace=True)

    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    columns = list(df.columns)[1:]
    weekly_data = []
    i = 0

    while i + 2 < len(columns):
        week_name = columns[i]
        target_col = columns[i]
        achieved_col = columns[i+2]

        weekly_data.append({
            "Week": week_name,
            "Target": df[target_col].sum(),
            "Achieved": df[achieved_col].sum()
        })

        i += 3

    weekly_df = pd.DataFrame(weekly_data)

    return df, weekly_df

import pandas as pd
import streamlit as st

st.title("📦 SKU to MSKU Mapper - WMS MVP")

# Upload files
sales_file = st.file_uploader("Upload Sales Data File (CSV or XLSX)", type=["csv", "xlsx"])
mapping_file = st.file_uploader("Upload SKU-MSKU Mapping File (CSV or XLSX)", type=["csv", "xlsx"])

def clean_column_names(df):
    df.columns = df.columns.str.strip().str.upper()
    return df

if sales_file and mapping_file:
    # Read sales data
    if sales_file.name.endswith('.csv'):
        sales_df = pd.read_csv(sales_file)
    else:
        sales_df = pd.read_excel(sales_file)

    # Read mapping data
    if mapping_file.name.endswith('.csv'):
        map_df = pd.read_csv(mapping_file)
    else:
        map_df = pd.read_excel(mapping_file)

    # Show original columns
    st.subheader("Sales Data Columns (Original):")
    st.write(sales_df.columns.tolist())
    st.subheader("Mapping Data Columns (Original):")
    st.write(map_df.columns.tolist())

    # Clean columns
    sales_df = clean_column_names(sales_df)
    map_df = clean_column_names(map_df)

    # Show cleaned columns
    st.subheader("Sales Data Columns (Cleaned):")
    st.write(sales_df.columns.tolist())
    st.subheader("Mapping Data Columns (Cleaned):")
    st.write(map_df.columns.tolist())

    # Auto-detect SKU columns in sales data (columns containing 'SKU')
    possible_sku_cols_sales = [col for col in sales_df.columns if 'SKU' in col]
    st.success(f"Detected SKU-like columns in Sales Data: {possible_sku_cols_sales}")

    # Let user select the SKU column from sales data
    selected_sales_sku_col = st.selectbox("Select SKU Column in Sales Data:", options=possible_sku_cols_sales)

    # For mapping data, let user pick which column to use as SKU/MSKU
    mapping_cols_options = map_df.columns.tolist()
    selected_map_sku_col = st.selectbox("Select SKU/MSKU Column in Mapping Data:", options=["None"] + mapping_cols_options)

    if selected_map_sku_col == "None":
        st.error("Please select a valid SKU or MSKU column from Mapping Data to proceed.")
    else:
        # Rename selected columns for merge
        sales_df = sales_df.rename(columns={selected_sales_sku_col: "SKU"})
        map_df = map_df.rename(columns={selected_map_sku_col: "SKU"})

        # Clean and convert to string to ensure matching works
        sales_df['SKU'] = sales_df['SKU'].astype(str).str.strip()
        map_df['SKU'] = map_df['SKU'].astype(str).str.strip()

        # Merge on SKU
        merged_df = pd.merge(sales_df, map_df, on="SKU", how="left", suffixes=('_sales', '_mapping'))

        # Check for missing MSKU or mapping values (in columns newly added from mapping)
        new_cols_from_map = [col for col in map_df.columns if col != 'SKU']
        missing_mask = merged_df[new_cols_from_map].isna().all(axis=1)
        missing_rows = merged_df[missing_mask]
        mapped_rows = merged_df[~missing_mask]

        st.success(f"✅ Successfully mapped {len(mapped_rows)} out of {len(merged_df)} rows.")
        st.warning(f"⚠️ {len(missing_rows)} rows could not be mapped from the mapping file.")

        st.subheader("🔍 Merged Data Preview:")
        st.dataframe(merged_df.head(50))

        # Download full merged output
        csv_full = merged_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Merged CSV", data=csv_full, file_name="merged_output.csv", mime="text/csv")

        # Optional: Download only missing rows
        if not missing_rows.empty:
            csv_missing = missing_rows.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Unmapped Rows", data=csv_missing, file_name="unmapped_skus.csv", mime="text/csv")

else:
    st.info("👆 Please upload both Sales Data and SKU Mapping files to start.")

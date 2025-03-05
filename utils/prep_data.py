import pandas as pd
import geopandas as gpd
import pyreadstat
import sys
from pathlib import Path
from pyarrow import parquet as pq
from sklearn.linear_model import LinearRegression
import numpy as np

# Ensure required dependencies are installed
try:
    import pyarrow.parquet
except ImportError:
    raise ImportError("❌ Missing required dependency: pyarrow. Install it using `pip install pyarrow`.")

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import config
from config import data_folder  

# Define directories
raw_data_folder = data_folder / "raw"
clean_data_folder = data_folder / "clean"
clean_data_folder.mkdir(parents=True, exist_ok=True)  # Ensure clean directory exists

# Define file paths
district_path = raw_data_folder / "district.gpkg"
state_path = raw_data_folder / "state.gpkg"
weights_path = raw_data_folder / "dist_pc11_pop_area_key.dta"
nightlights_path_1 = raw_data_folder / "viirs_annual_pc11dist_2012_2023.dta"
nightlights_path_2 = raw_data_folder / "dmsp_pc11dist_1994_2013..dta"
pm25_path = raw_data_folder / "pm25_pc11dist_1998_2020.dta"
vcf_path = raw_data_folder / "vcf_pc11dist_2001_2020.dta"

data_parquet_path = clean_data_folder / "final_data.parquet"

def nightlights_data():
    print(f"✅ Loading Stata file from {nightlights_path_1}")
    # Read the first nightlights file
    # Load the datasets
    df1, _ = pyreadstat.read_dta(nightlights_path_1)  # VIIRS data
    df2, _ = pyreadstat.read_dta(nightlights_path_2)  # DMSP data

    # Filter VIIRS to keep only "median-masked" category
    df1 = df1[df1["category"] == "median-masked"]
    df1 = df1[["year", "pc11_district_id", "viirs_annual_mean"]].rename(columns={"viirs_annual_mean": "nightlights"})

    # Sort and keep the latest DMSP version
    df2 = df2.sort_values(["year", "pc11_district_id", "dmsp_f_version"], ascending=[True, True, False])
    df2 = df2.drop_duplicates(subset=["year", "pc11_district_id"], keep="first")
    df2 = df2[["year", "pc11_district_id", "dmsp_mean_light_cal"]].rename(columns={"dmsp_mean_light_cal": "nightlights"})

    # Identify overlapping years (2012-2013) for intercalibration
    df_overlap = df1.merge(df2, on=["year", "pc11_district_id"], suffixes=("_viirs", "_dmsp"))
    df_overlap = df_overlap[(df_overlap["year"] >= 2012) & (df_overlap["year"] <= 2013)].dropna()

    # Apply log transformation (avoid log(0) by adding a small constant)
    df_overlap["log_viirs"] = np.log(df_overlap["nightlights_viirs"] + 1e-6)
    df_overlap["log_dmsp"] = np.log(df_overlap["nightlights_dmsp"] + 1e-6)

    # Fit log-linear regression model
    X = df_overlap["log_dmsp"].values.reshape(-1, 1)
    y = df_overlap["log_viirs"].values.reshape(-1, 1)
    model = LinearRegression().fit(X, y)

    alpha, beta = model.intercept_[0], model.coef_[0][0]
    print(f"Log-Linear Regression Parameters: α = {alpha:.4f}, β = {beta:.4f}")

    # Apply transformation to pre-2012 DMSP data
    df2_pre2012 = df2[df2["year"] < 2012].copy()
    df2_pre2012["nightlights"] = np.exp(alpha + beta * np.log(df2_pre2012["nightlights"] + 1e-6))

    # Combine harmonized DMSP and VIIRS data
    nightlights = pd.concat([df1, df2_pre2012])

    # Filter for required years
    nightlights = nightlights[(nightlights["year"] >= 2001) & (nightlights["year"] <= 2020)]
    nightlights["log_nightlights"] = np.log1p(nightlights["nightlights"])  # Equivalent to log(1 + x)



    return nightlights

def vcf_data():
    print(f"✅ Loading Stata file from {vcf_path}")
    # Read the VCF file
    df, _ = pyreadstat.read_dta(vcf_path)
    # Select relevant columns and rename them
    df = df[["year", "pc11_district_id", "vcf_mean"]].rename(columns={"vcf_mean": "forest_cover"})

    # Filter the dataset for the required years
    df = df[(df["year"] >= 2001) & (df["year"] <= 2020)]
    df["log_forest_cover"] = np.log1p(df["forest_cover"])  # Equivalent to log(1 + x)


    return df

def pm25_data():
    print(f"✅ Loading Stata file from {pm25_path}")
    # Read the PM25 file
    df, _ = pyreadstat.read_dta(pm25_path)
    # Select relevant columns
    df = df[["year", "pc11_district_id", "pm25_mean"]].rename(columns={"pm25_mean": "pm25"})

    # Filter the dataset for the required years
    df = df[(df["year"] >= 2001) & (df["year"] <= 2020)]
    df["log_pm25"] = np.log1p(df["pm25"])  # Equivalent to log(1 + x)

    return df

def merge_and_save_data():
    # Load all datasets
    nightlights = nightlights_data()
    vcf = vcf_data()
    pm25 = pm25_data()

    # Check if the state GeoPackage file exists
    if not state_path.exists():
        raise FileNotFoundError(f"❌ GeoPackage not found: {state_path}")
    
    print(f"✅ Loading India boundaries from {state_path}")
    # Load state and district boundaries
    state = gpd.read_file(state_path)
    district = gpd.read_file(district_path)

    # Merge district and state to get state name
    district = district.merge(state[["pc11_state_id", "state_name"]], on="pc11_state_id", how="left")

    # Keep only the required columns
    district = district[["pc11_state_id", "pc11_district_id", "district_name", "state_name"]].rename(columns={"district_name": "district", "state_name": "state"})

    # Filter out invalid district IDs
    district = district[district["pc11_district_id"] != "000"]

    weights = pd.read_stata(weights_path)
    # Aggregate data at state level
    state_weights = weights.groupby("pc11_state_id", as_index=False).agg({"dist_pc11_pca_tot_p": "sum", "dist_pc11_land_area": "sum"})

    # Compute tertiles for categorization
    state_weights["area_cat"] = pd.qcut(state_weights["dist_pc11_land_area"], q=[0, 1/3, 2/3, 1], labels=["Small", "Medium", "Large"])
    state_weights["pop_cat"] = pd.qcut(state_weights["dist_pc11_pca_tot_p"], q=[0, 1/3, 2/3, 1], labels=["Low", "Medium", "High"])

    # Merge back to the district-level dataset
    weights = weights.merge(state_weights[["pc11_state_id", "area_cat", "pop_cat"]], on="pc11_state_id", how="left")

    # Select relevant columns
    weights = weights[["pc11_district_id", "dist_pc11_pca_tot_p", "dist_pc11_land_area", "area_cat", "pop_cat"]].rename(columns={"dist_pc11_pca_tot_p": "pop11", "dist_pc11_land_area": "area"})
    weights["log_area"] = np.log(weights["area"])
    weights["log_pop11"] = np.log(weights["pop11"])  # Equivalent to log(1 + x)
    # print(weights.columns)

    



    # Merge all datasets
    final_dataset = (district
                 .merge(weights, on="pc11_district_id", how="left")
                 .merge(nightlights, on="pc11_district_id", how="left")
                 .merge(vcf, on=["pc11_district_id", "year"], how="left")
                 .merge(pm25, on=["pc11_district_id", "year"], how="left"))
    
    # Convert the 'year' column to integer
    final_dataset["year"] = final_dataset["year"].astype(int)

    print(f"💾 Saving data to {data_parquet_path}")
    
    # Save the final dataset to a Parquet file
    final_dataset.to_parquet(data_parquet_path, engine="pyarrow")

if __name__ == "__main__":
    merge_and_save_data()
    print("🎉 All conversions and saves completed successfully!")
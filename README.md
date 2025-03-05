# Data Processing and Dashboard for District-Level Analysis  

## Folder Structure  
```bash
├── app.py # Dash application
├── config.py # Configuration settings
├── data/
│ ├── raw/ # Raw datasets (not included)
│ ├── clean/ # Processed datasets
│ │ ├── final_data.parquet # Merged dataset used in the dashboard
├── utils/
│ ├── init.py
│ ├── cache.py # Caching utilities
│ ├── prep_data.py # Script for merging datasets
├── LICENSE
├── README.md
├── requirements.txt # List of required Python libraries
```


## Overview  

This project processes district-level SHRUG data (2001-2020) and hosts a Dash application for tabulation and visualization.  

- The raw data files should be stored in `data/raw/`. They can be downloaded from [https://www.devdatalab.org/shrug_download/](https://www.devdatalab.org/shrug_download/) These include:  
  - SHRUG PC11 district weights key: `dist_pc11_pop_area_key.dta`
  - SHRUG VIIRS Night Lights (2012 - 2021): `viirs_annual_pc11dist_2012_2023.dta` 
  - SHRUG PC11 District Polygons: `district.gpkg`  
  - SHRUG Vegetation Continuous Fields (VCF): `vcf_pc11dist_2001_2020.dta`  
  - SHRUG PC11 State Polygons: `state.gpkg`  
  - SHRUG Surface PM 2.5: `pm25_pc11dist_1998_2020.dta`  
  - SHRUG DMSP Night Lights (1992 - 2013): `dmsp_pc11dist_1994_2013.dta`  

- The script `utils/prep_data.py` merges these datasets into a single processed dataset stored in `data/clean/final_data.parquet`.  

- The `app.py` file runs the Dash application using the cleaned dataset and raw files do not need to be downloaded to run the app.  

## Github Link: 

[https://github.com/sr-eco/Trial_render.git](https://github.com/sr-eco/Trial_render.git)

## Dashboard  

The dashboard is hosted on a **low-RAM free tier environment** at:  
[https://trial-render-w5z9.onrender.com](https://trial-render-w5z9.onrender.com)  

## Running the app locally

The dashboard is built to run on Python 3.13.2. To start the application, install the requirements and run app.py as follows:


```bash
pip install -r requirements.txt
python app.py
```

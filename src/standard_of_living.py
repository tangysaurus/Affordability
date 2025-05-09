import pandas as pd

# reads in a file, converts it to a dataframe, & cleans it
def process(file_path):
    df = pd.read_csv(file_path)

    if df.isnull().values.any():
        df.fillna(0, inplace = True)

    for column in df.columns:
        if pd.api.types.is_string_dtype(df[column]):
            df[column] = df[column].str.strip()
    
    return df

# processes and merges datasets
def run():
    # process wage & rpp data
    wage_data = process("data/regional_salaries.csv")
    rpp_data = process("data/regional_prices.csv")
    # merge datasets on GeoFIPS
    merged = pd.merge(wage_data, rpp_data, on = "GeoFIPS")
    merged = merged.drop(columns = ["GeoFIPS", "Occupation Code", "GeoName_y"])
    # calculate median purchasing power
    merged["Median Purchasing Power"] = (merged["Annual Salary Median"].astype(float) / merged["RPP 2023"].astype(float) / 100).round(2)
    # rename & get relevant columns
    merged = merged.rename(columns = {"GeoName_x" : "Area", "Description" : "Category"})
    merged = merged[["Area", "Occupation Title", "Annual Salary Median", "Category", "RPP 2023", "Median Purchasing Power"]]
    return merged

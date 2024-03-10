import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
filename = "data/airports-updated.dat"
filepath = filename

df = pd.read_csv(filepath, index_col='Airport ID')
print(df.head(5))
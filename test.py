from oracle import get_data_from
import pandas as pd

df = get_data_from('ASSEMBLING_PARAMS')
print(df.head())
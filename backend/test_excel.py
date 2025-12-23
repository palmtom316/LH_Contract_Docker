
import pandas as pd
import os

try:
    df = pd.DataFrame({'A': [1, 2, 3]})
    with pd.ExcelWriter('test.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    print("Success")
except Exception as e:
    print(f"Error: {e}")

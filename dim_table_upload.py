import pandas as pd
import snowflake.connector
from snowflake.snowpark import Session

conn_param = {
    "user": '',
    "password": '',
    "account": '',
    "role": "ACCOUNTADMIN",
    "warehouse": 'COMPUTE_WH',
    "database": 'STOCK_PROJECT',
    "schema": 'dimension'
}

# Create the Snowflake Snowpark session
ses = Session.builder.configs(conn_param).create()


df1 = pd.read_csv("./Member_Dimensions.csv")
ses.write_pandas(df1, table_name='MEMBER_DIMENSION', schema='DIMENSION', overwrite=True)
print('updated member dim')

df2 = pd.read_csv("./Holiday_Dim.csv")
df2['DATE'] = pd.to_datetime(df2['DATE'], format='%B %d %Y', errors='coerce').dt.strftime('%Y-%m-%d')
print(df2)
ses.write_pandas(df2, table_name='HOLIDAY_DIMENSION',schema='DIMENSION', overwrite=True)
print('updated holiday dim')

df3 = pd.read_csv("./EQUITY_L.csv")
ses.write_pandas(df3, table_name='SYMBOL_DIMENSION',schema='DIMENSION',overwrite=True)
print('updated symbol dim')


import datetime

import pandas as pd
import datetime as dt
import yfinance as yf

from snowflake.snowpark import Session

# Snowflake connection parameters
conn_param = {
    "user": '',
    "password": '',
    "account": '',
    "role": "ACCOUNTADMIN",
    "warehouse": 'COMPUTE_WH',
    "database": 'STOCK_PROJECT',
    "schema": 'DIMENSION'
}

# Establish connection
ses = Session.builder.configs(conn_param).create()

pd.set_option("display.max_columns", None)


def getSymbols():
    data = ses.sql("SELECT symbol from dimension.symbol_dimension").collect()

    symbols = [line[0] for line in data]

    return symbols


def getStockData(symbols, start_date, end_date):
    print("getting data...")
    record = []
    #symbols = symbols[0:1000]  # For testing first 1000 stocks
    for sym in symbols:
        try:
            sdata = yf.Ticker(sym + ".NS").history(start=start_date, end=end_date)
            if sdata.empty:
                print(f"No data available for {sym}. Skipping.")
                continue

            for date, data in sdata.iterrows():
                record.append([
                    date.strftime("%Y-%m-%d"),
                    sym,
                    data['Open'],
                    data['High'],
                    data['Low'],
                    data['Close'],
                    data['Volume'],
                    ((data['Close'] * data['Volume']) / 10 ** 7),  # turnover
                    data['Dividends'],
                    data['Stock Splits']
                ])
        except Exception as e:
            print(f"Error fetching data for {sym}: {e}")
            continue  # Skip this symbol if an error occurs

    return record



def main():
    symbols = getSymbols()

    start_date = dt.date(2024, 1, 1)
    end_date = dt.datetime.now().date()

    print(start_date, end_date)
    record = getStockData(symbols, start_date, end_date)
    # print(record)
    df1= pd.DataFrame(record,columns=['DATE', 'SYMBOL', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'TURN_OVER', 'DIVIDENDS', 'STOCK_SPLITS'])
    print(df1)
    ses.write_pandas(df1,table_name='STOCK_DAILY_STAGING',schema='STAGING',overwrite=True)
    #     #print(staging_data)])




if __name__ == "__main__":
    user_choice = input("Press 'A' to generate data from hardcoded date : ").strip().upper()

    if user_choice == 'A':
        main()
    else:
        # Get max date from staging
        result = ses.sql("SELECT MAX(date) AS max_date FROM STAGING.STOCK_DAILY_STAGING").collect()
        max_date = result[0]['MAX_DATE']
        current_date = dt.date.today()

        # Set start date as next day of max date
        start_date = max_date + dt.timedelta(days=1)

        print(f"Updating staging table with data from {start_date} to {current_date}")

        # Get symbols and fetch stock data
        symbols = getSymbols()
        record = getStockData(symbols, start_date, current_date)

        # Store dataframe in a variable
        df_update = pd.DataFrame(record, columns=[
            'DATE', 'SYMBOL', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME', 'TURN_OVER', 'DIVIDENDS', 'STOCK_SPLITS'
        ])

        # Load into staging table
        ses.write_pandas(df_update, table_name='STOCK_DAILY_STAGING', schema='STAGING', overwrite=False)

        print(df_update)

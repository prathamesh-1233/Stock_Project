import datetime as dt
import pandas as pd
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

# Helpers
def isWeekendFind(date):
    return 1 if date.strftime('%A') in ['Saturday', 'Sunday'] else 0

def quarterFind(date):
    if date.month in [1, 2, 3]:
        return 'Q1'
    elif date.month in [4, 5, 6]:
        return 'Q2'
    elif date.month in [7, 8, 9]:
        return 'Q3'
    else:
        return 'Q4'

# Generate calendar_dimension data
def calendar(ses, start_date, end_date):

    lst = []

    while start_date <= end_date:
        record = (
            start_date,
            start_date.day,
            start_date.strftime('%A'),
            isWeekendFind(start_date),
            start_date.isocalendar()[1],
            start_date.strftime('%B'),
            start_date.month,
            quarterFind(start_date),
            start_date.year
        )
        #cursor.execute(insert_query, record)
        lst.append(record)
        start_date += dt.timedelta(days=1)

    df1 = pd.DataFrame(lst,columns=["DATE", "DAY_OF_MONTH", "DAY_OF_WEEK", "IS_WEEKEND","WEEK_OF_YEAR", "MONTH", "MONTH_NUMBER", "QUARTER","YEAR"])
    ses.write_pandas(df1,table_name="CALENDAR_DIMENSION",schema='DIMENSION',overwrite=True)

    print("calendar_dimension updated")


# Insert into trading_dimension by filtering non-weekend and non-holiday
def tradingDimension(cursor):
    insert_query = """
        INSERT INTO dimension.trading_dimension (DATE, DAY_OF_MONTH, DAY_OF_WEEK, IS_WEEKEND,
                                                 WEEK_OF_YEAR, MONTH, MONTH_NUMBER, QUARTER, YEAR)
        SELECT 
            DATE,
            DAY_OF_MONTH,
            DAY_OF_WEEK,
            IS_WEEKEND,
            WEEK_OF_YEAR,
            MONTH,
            MONTH_NUMBER,
            QUARTER,
            YEAR
        FROM dimension.calendar_dimension cd
        WHERE cd.DATE NOT IN (SELECT DATE FROM dimension.holiday_dimension)
        AND cd.IS_WEEKEND = 0
    """
    ses.sql(insert_query).collect()
    print('Trading dim updated')


# Main function
def main():
    start_date = dt.date(2023, 1, 1)
    end_date = dt.date(2025, 12, 31)

    calendar(ses,start_date, end_date)

    tradingDimension(ses)


if __name__ == "__main__":
    main()

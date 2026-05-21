import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",
    database="import_export"
)

fact_trade = pd.read_sql("SELECT * FROM fact_trade", conn)
dim_product = pd.read_sql("SELECT * FROM dim_product", conn)
dim_hs2 = pd.read_sql("SELECT * FROM dim_hs2", conn)
dim_year = pd.read_sql("SELECT * FROM dim_year", conn)
dim_tradetype = pd.read_sql("SELECT * FROM dim_tradetype", conn)

conn.close()
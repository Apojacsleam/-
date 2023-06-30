import akshare as ak
import pandas as pd
from sqlalchemy import create_engine
import tushare as ts
import pymysql

def GetProApi():
    conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading", password="trading_1",
                           database="stocktrading")
    cursor = conn.cursor()
    cursor.execute('select * from proapi')
    data = cursor.fetchall()[0][0]
    cursor.close()
    conn.close()
    return data


def GetStockInfo():
    """
    获取股票信息并整理数据

    Returns:
        DataFrame: 整理后的股票信息数据
    """
    # 使用akshare库获取A股实时数据
    df = ak.stock_zh_a_spot_em()
    # 选择所需字段
    df = df[['代码', '昨收', '最新价', '涨跌幅']]
    df.columns = ['stock_id', 'closing_price_y', 'open_price_t', 'change_extent']
    # 使用tushare库获取股票基本信息
    pro = ts.pro_api(GetProApi())
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    # 筛选上交所和深交所的股票信息
    data['suffix'] = data['ts_code'].str[-3:]
    data = data[data['suffix'].isin(['.SZ', '.SH'])]
    data['suffix'] = data['suffix'].replace({'.SZ': '深证', '.SH': '上证'})
    data = data[['symbol', 'name', 'list_date', 'suffix', 'industry']]
    data.columns = ['stock_id', 'stock_name', 'issuance_time', 'stock_type', 'block']
    # 合并股票实时数据和股票基本信息
    Data = pd.merge(data, df, on='stock_id')
    Data = Data[['stock_id', 'stock_name', 'issuance_time', 'closing_price_y', 'open_price_t', 'stock_type', 'block', 'change_extent']]
    # 删除包含缺失值的行
    Data = Data.dropna()
    return Data


def upHold():
    """
    更新并保存股票信息到数据库

    Returns:
        None
    """
    engine = create_engine('mysql+pymysql://trading:trading_1@tradingsystem.mysql.polardb.rds.aliyuncs.com/stocktrading')
    with engine.begin() as connection:
        connection.execute('SET FOREIGN_KEY_CHECKS = 0')  # 禁用外键检查
        connection.execute('DELETE FROM stock_info')
        connection.execute('SET FOREIGN_KEY_CHECKS = 1')  # 启用外键检查
    # 获取最新的股票信息数据
    Data = GetStockInfo()
    # 将数据保存到数据库中的stock_info表
    Data.to_sql('stock_info', con=engine, if_exists='append', index=False)

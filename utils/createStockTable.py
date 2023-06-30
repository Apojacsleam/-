import pymysql
import tushare as ts
from utils import getHistoryData


def createStockTable(t):
    """
    创建股票表格

    Args:
        t (str): 表格名称

    Returns:
        None
    """
    # 连接数据库
    conn = pymysql.connect(
        host="tradingsystem.mysql.polardb.rds.aliyuncs.com",
        port=3306,
        user="trading",
        password="trading_1",
        database="stocktrading"
    )
    cursor = conn.cursor()

    # 创建SQL语句
    sql = """CREATE TABLE `%s`(
                 TRADING_DAY VARCHAR(64) DEFAULT NULL,
                 OPEN_PRICE FLOAT DEFAULT NULL,
                 HIGHEST FLOAT DEFAULT NULL,
                 LOWEST FLOAT DEFAULT NULL,
                 CLOSE_PRICE FLOAT DEFAULT NULL)
                """

    # 执行SQL语句
    cursor.execute(sql, [t])


def createEvedayTable(t):
    """
    创建每日表格

    Args:
        t (str): 表格名称

    Returns:
        None
    """
    # 连接数据库
    conn = pymysql.connect(
        host="tradingsystem.mysql.polardb.rds.aliyuncs.com",
        port=3306,
        user="trading",
        password="trading_1",
        database="stocktrading"
    )
    cursor = conn.cursor()

    # 创建SQL语句
    sql = """CREATE TABLE `%s`(
                 DAILY_TICKS VARCHAR(64) DEFAULT NULL,
                 REAL_TIME_QUOTES FLOAT DEFAULT NULL
                 )
                """

    # 执行SQL语句
    cursor.execute(sql, ["dailyTicks_" + t])
    cursor.close()
    conn.close()


def InsertOldDay(t):
    """
    插入历史数据

    Args:
        t (str): 表格名称

    Returns:
        None
    """
    # 获取历史数据
    res = getHistoryData.getHistoryData(t)
    print(res)

    # 连接数据库
    conn = pymysql.connect(
        host="tradingsystem.mysql.polardb.rds.aliyuncs.com",
        port=3306,
        user="trading",
        password="trading_1",
        database="stocktrading"
    )
    cursor = conn.cursor()

    # 创建SQL语句
    sql = "INSERT INTO `%s`(TRADING_DAY,OPEN_PRICE,HIGHEST,LOWEST,CLOSE_PRICE) VALUES(%s, %s, %s, %s,%s)"
    t = t.split(".")

    # 插入数据
    for i in res:
        i.insert(0, t[0] + "_" + t[1])
        cursor.execute(sql, i)
        conn.commit()
    cursor.close()
    conn.close()


def insertTodayTickData(t):
    """
    插入当日股票交易数据

    Args:
        t (str): 股票代码

    Returns:
        None
    """
    # 根据股票代码获取当日交易数据
    t = t.split(".")
    res = ts.get_today_ticks(t[0])

    # 连接数据库
    conn = pymysql.connect(
        host="tradingsystem.mysql.polardb.rds.aliyuncs.com",
        port=3306,
        user="trading",
        password="trading_1",
        database="stocktrading"
    )
    cursor = conn.cursor()

    # 创建SQL语句
    sql = "INSERT INTO `%s`(TRADING_DAY,OPEN_PRICE,HIGHEST,LOWEST,CLOSE_PRICE) VALUES(%s, %s, %s, %s,%s)"

    # 插入数据
    for i in res:
        i.insert(0, t[0] + "_" + t[1])
        cursor.execute(sql, i)
        conn.commit()
    cursor.close()
    conn.close()


def getTscode():
    """
    获取股票代码

    Returns:
        None
    """
    # 连接数据库
    conn = pymysql.connect(
        host="tradingsystem.mysql.polardb.rds.aliyuncs.com",
        port=3306,
        user="trading",
        password="trading_1",
        database="stocktrading"
    )
    cursor = conn.cursor()

    # 查询股票信息
    sql = "select stock_id,stock_type  from stock_info"
    cursor.execute(sql)
    stoinfo = cursor.fetchall()

    # 遍历股票信息，插入历史数据
    for i in range(959, len(stoinfo)):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "_" + "SH"
        else:
            tmp = stoinfo[i][0] + "_" + "SZ"
        InsertOldDay(tmp)

    cursor.close()
    conn.close()

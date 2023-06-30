import tushare as ts
import numpy as np
import datetime
import pymysql


def judge():
    """
    判断当前时间是否为A股交易时间

    Returns:
        bool: 如果是A股交易时间则返回True，否则返回False
    """
    # 获取当前日期和时间
    now = datetime.datetime.now()

    # 构造上午和下午的交易时间范围
    morning_start_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    morning_end_time = now.replace(hour=11, minute=30, second=0, microsecond=0)
    afternoon_start_time = now.replace(hour=13, minute=0, second=0, microsecond=0)
    afternoon_end_time = now.replace(hour=15, minute=0, second=0, microsecond=0)

    # 判断当前时间是否在交易时间范围内
    if now.weekday() < 5 and ((morning_start_time <= now <= morning_end_time) or (afternoon_start_time <= now <= afternoon_end_time)):
        return True
    else:
        return False


def clearTodayData():
    """
    清除当天的股票数据。

    该函数将连接数据库，并删除所有股票的当天数据。
    """
    conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading", password="trading_1",
                           database="stocktrading")
    cursor = conn.cursor()
    sql = "DELETE FROM `%s`"
    stoinfo = getTscode()
    # 循环遍历股票信息并执行删除操作
    for i in range(0, len(stoinfo)):
        cursor.execute(sql, ["daily_ticks" + "_" + stoinfo[i][0] + "_" + stoinfo[i][0]])


def getTodayRealTimeData():
    """
    获取今天的实时数据并存入数据库中。

    使用tushare库获取股票实时行情信息，将相关数据插入到MySQL数据库中。

    参数：
    无

    返回：
    无
    """
    # 连接数据库
    conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading",
                           password="trading_1", database="stocktrading")
    cursor = conn.cursor()
    # 获取股票代码信息
    stoinfo = getTscode()
    # SQL语句模板
    sql = "INSERT INTO `%s`(DAILY_TICKS,REAL_TIME_QUOTES) VALUES(%s, %s)"
    # 循环获取实时数据
    while (1):
        if judge():
            for i in range(0, len(stoinfo)):
                if (i != 2190):
                    # 获取股票实时行情
                    df = ts.get_realtime_quotes(symbols=stoinfo[i][0])
                    df = df[['code', 'name', 'price', 'bid', 'ask', 'volume', 'amount', 'time']]
                    print(df)
                    # 处理数据
                    res = np.array(df)
                    res = res[:, [2, 7]]

                    if (len(res) != 0):
                        if (stoinfo[i][1] == "深证"):
                            # 插入深证股票数据
                            cursor.execute(sql, ["dailyticks_" + stoinfo[i][0] + "_" + "SZ", res[0][1], res[0][0]])
                        else:
                            # 插入上证股票数据
                            cursor.execute(sql, ["dailyticks_" + stoinfo[i][0] + "_" + "SH", res[0][1], res[0][0]])
                    conn.commit()
        # 判断是否超过晚上15:00自动终止获取
        n_time = datetime.now()
        end = datetime.strptime(str(datetime.now().date()) + "15:00", '%Y-%m-%d%H:%M')
        if n_time > end:
            break
    cursor.close()
    conn.close()


def getTscode():
    """
    获取股票代码和类型信息

    Returns:
        list: 包含股票代码和类型的元组列表
    """
    # 连接数据库
    conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading", password="trading_1",
                           database="stocktrading")
    # 创建游标对象
    cursor = conn.cursor()
    # SQL查询语句
    sql = "select stock_id, stock_type from stock_info"
    # 执行查询
    cursor.execute(sql)
    # 获取查询结果
    stoinfo = cursor.fetchall()
    # 关闭游标
    cursor.close()
    # 关闭数据库连接
    conn.close()
    return stoinfo

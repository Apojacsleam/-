import pymysql
import tushare as ts
import numpy as np
import time


def portinStockInfo(t):
    """
    将股票信息导入数据库。

    参数:
        t (str): 股票代码。

    返回:
        无返回值。

    """
    # 连接数据库
    conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading", password="trading_1",
                           database="stocktrading")
    # 创建游标
    cursor = conn.cursor()
    # SQL语句
    sql = "INSERT INTO stock_info(stock_id,stock_name,issuance_time,block,stock_type) VALUES(%s, %s, %s, %s,%s)"
    # 获取股票信息
    data = getStockInfo(t)
    for i in data:
        # 添加股票类型为"上证"
        i.append("上证")
        # 执行SQL语句
        cursor.execute(sql, i)
    # 提交事务
    conn.commit()
    # 关闭游标和连接
    cursor.close()
    conn.close()


def getStockInfo(t):
    """
    获取股票信息。

    参数:
        t (str): 交易所代码。

    返回:
        list: 包含股票信息的列表，每个元素是一个包含股票代号、名称、上市日期和板块的子列表。

    """
    # 使用tushare模块创建API对象
    pro = ts.pro_api('75511519160650be789a0f32b316368fddf2474c0d32f563253d91e9')
    # 获取股票基本信息
    data = pro.stock_basic(exchange=t, list_status='L', fileds='ts_code,symbol,name,list_date,market')
    # 将DataFrame转换为NumPy数组
    data = np.array(data)
    # 选择需要的列并重新组织数据
    data = data[:, [1, 2, 6, 5]]  # 代号，名称，上市日期，板块
    # 将NumPy数组转换为列表
    data = data.tolist()
    return data


def getEveDayPrice(t):
    """
    获取当日股票收盘价。

    参数:
        t (str): 股票代码。

    返回:
        list: 包含当日股票收盘价的列表，每个元素是一个包含日期、开盘价和收盘价的子列表。

    """
    # 使用tushare模块创建API对象
    pro = ts.pro_api('75511519160650be789a0f32b316368fddf2474c0d32f563253d91e9')
    # 获取当前日期
    strt = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    # 将日期字符串拆分为年、月、日
    strt = strt.split("-")
    # 获取股票每日行情数据
    df = pro.daily(ts_code=t, start_date=strt[0] + strt[1] + strt[2], end_date=strt[0] + strt[1] + strt[2])
    # 将DataFrame转换为NumPy数组
    df = np.array(df)
    # 选择需要的列并重新组织数据
    df = df[:, [2, 6, 8]]  # 日期，开盘价，收盘价
    # 将NumPy数组转换为列表
    df = df.tolist()
    return df


def updateEveryday(t):
    """
    更新每日股票信息。

    参数:
        t (str): 股票代码。

    返回:
        无返回值。

    """
    # 获取当日股票收盘价数据
    df = getEveDayPrice(t)
    # 如果收盘价数据不为空
    if len(df) != 0:
        # 取第一条数据（当日收盘价）
        df = df[0]
        # 连接数据库
        conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading", password="trading_1",
                               database="stocktrading")
        # 创建游标
        cursor = conn.cursor()
        # SQL语句
        sql = "update stock_info set closing_price_y='%s' ,open_price_t='%s',change_extent='%s' where stock_id=%s"
        # 获取股票代号
        symbol = t.split(".")
        # 将股票代号添加到收盘价数据中
        df.append(symbol[0])
        # 执行SQL语句
        cursor.execute(sql, df)
        # 提交事务
        conn.commit()
        # 关闭游标和连接
        cursor.close()
        conn.close()


def getTscode():
    """
    从数据库中获取股票代码列表，并执行更新操作。
    """
    # 连接数据库
    conn = pymysql.connect(host="tradingsystem.mysql.polardb.rds.aliyuncs.com", port=3306, user="trading", password="trading_1",
                           database="stocktrading")
    cursor = conn.cursor()
    # 查询股票信息
    sql = "select stock_id,stock_type  from stock_info"
    cursor.execute(sql)
    stoinfo = cursor.fetchall()
    # 更新股票信息
    for i in range(0, 500):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(500, 1000):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(1000, 1500):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(1500, 2000):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(1500, 2000):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(2000, 2500):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(2500, 3000):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(3000, 3500):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    time.sleep(120)  # 等待时间
    for i in range(3500, 3754):
        if (stoinfo[i][1] == "上证"):
            tmp = stoinfo[i][0] + "." + "SH"
        else:
            tmp = stoinfo[i][0] + "." + "SZ"
        updateEveryday(tmp)
    # 关闭数据库连接
    cursor.close()
    conn.close()

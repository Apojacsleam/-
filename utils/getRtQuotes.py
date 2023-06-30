import tushare as ts
import numpy as np
import time
from datetime import date
from chinese_calendar import is_workday, is_holiday


def getworkday():
    """判断当前日期是否为工作日"""
    strt = time.strftime('%Y-%m-%d', time.localtime(time.time()))

    strt = strt.split("-")
    y = int(strt[0])
    m = int(strt[1])
    d = int(strt[2])

    april_last = date(y, m, d)
    return is_workday(april_last) and (not is_holiday(april_last))


def getRtQuotes(t):
    """
    获取实时行情数据

    参数:
        t (str): 股票代码

    返回值:
        tuple: 包含三个元素的元组，第一个元素表示操作结果(1表示成功获取行情数据，0表示未能获取行情数据)，第二个元素是股票代码列表，第三个元素是对应的行情数据列表
    """
    f = getworkday()
    # 初始化行情数据为空
    resx = "0"
    resy = "0"
    if f:
        # 获取当天实时交易数据
        df = ts.get_today_ticks(t)
        res = np.array(df)
        # 提取股票代码和行情数据
        resx = res[:, [0]]
        resy = res[:, [1]]
        # 将数据转换为一维数组
        resx = resx.reshape(-1)
        resy = resy.reshape(-1)
        # 转换为列表形式
        resx = resx.tolist()
        resy = resy.tolist()
        return 1, resx, resy
    else:
        return 0, resx, resy

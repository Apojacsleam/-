import tushare as ts
import numpy as np
import time


def getHistoryData(t):
    """
    通过tushare API获取指定股票代码的历史数据。

    参数:
        t (str): 股票代码

    返回值:
        list: 包含历史数据的列表，每个元素是一个包含日期、开盘价、最高价、最低价和收盘价的子列表。
    """

    pro = ts.pro_api('75511519160650be789a0f32b316368fddf2474c0d32f563253d91e9')
    strt = time.strftime('%Y-%m-%d', time.localtime(time.time()))

    strt = strt.split("-")

    # 从tushare获取股票历史数据
    df = pro.daily(ts_code=t, start_date='20190101', end_date=strt[0] + strt[1] + strt[2])
    print(df)

    # 使用numpy处理数据
    res = np.array(df)
    # 重新排序列，按照日期、开盘价、最高价、最低价、收盘价的顺序
    res = res[:, [1, 2, 5, 4, 3]]
    # 转换为列表格式
    res = res.tolist()

    return res

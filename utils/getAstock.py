import tushare as ts
import numpy as np
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


def getAstock(t):
    """
    获取股票数据，并返回包含股票代码和持有量的列表。

    参数：
    t (str): 股票代码

    返回值：
    list: 包含股票代码和持有量的列表，格式为[[股票代码1, 持有量1], [股票代码2, 持有量2], ...]
    """
    # 使用tushare库获取股票数据
    pro = ts.pro_api(GetProApi())
    df = pro.stk_rewards(ts_code=t)
    # 删除含有缺失值的行
    m = df.dropna(axis=0)
    # 删除持有量为0的行
    m = m[~m['hold_vol'].isin([0])]
    # 将DataFrame转换为NumPy数组
    res = np.array(m)
    # 提取第1列和第4列，并限制结果为前5行
    res = res[0:5, [3, 6]]
    # 创建一个空字典
    dic = {}
    # 将NumPy数组转换为列表
    res = list(res)
    # 遍历列表中的每个元素，将第1列作为键，第2列作为值，存入字典中
    for i in range(0, len(res)):
        dic[res[i][0]] = res[i][1]
    # 创建一个空列表
    res = []
    # 遍历字典中的每个键值对，将键和值组成一个列表，添加到结果列表中
    for key in dic:
        tmp = []
        tmp.append(key)
        print(key, dic[key])
        tmp.append(dic[key])
        res.append(tmp)
    return res

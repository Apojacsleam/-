from my_fake_useragent import UserAgent  # 导入第三方库：my_fake_useragent
import re  # 导入正则表达式库：re
from urllib import request  # 导入urllib库中的request模块

def gen_news():
    """
    生成新闻函数，从指定网页中获取新闻标题和内容，并以字典形式返回。

    Returns:
        list: 包含新闻标题和内容的字典列表
    """

    ua = UserAgent()  # 创建UserAgent对象
    user_agent = ua.random()  # 随机生成User-Agent

    referer = 'https://tushare.pro/login?next=%2Fnews%2Fnews_sina'  # 设置referer字段

    headers = {
        'User-Agent': user_agent,  # 设置请求头的User-Agent字段
        'Host': 'tushare.pro',  # 设置请求头的Host字段
        'Origin': 'https://tushare.pro',  # 设置请求头的Origin字段
        'Referer': referer  # 设置请求头的Referer字段
    }

    stockPageRequest = request.urlopen('http://finance.eastmoney.com/news/cdfsd.html')  # 发送请求获取股票新闻网页内容
    htmlTitleContent = str(stockPageRequest.read(), 'utf-8')  # 将网页内容转换成UTF-8编码的字符串

    titlePattern = re.compile('<span class="l3 a3">title="(.*?)"</span>', re.S)  # 编译正则表达式，用于匹配标题
    p_title = 'title="(.*?)"(.*?)'  # 正则表达式匹配模式
    title = re.findall(p_title, htmlTitleContent)  # 通过正则表达式匹配获取所有标题
    title = [t[0] for t in title if not t[0].find('【')]  # 筛选标题中包含"【"的部分

    news = []
    for t in title:
        a = t.find('【')  # 找到标题中"【"的位置
        b = t.find('】')  # 找到标题中"】"的位置
        news.append({'title': t[a+1:b], 'content': t[b+1:]})  # 将标题和内容添加到news列表中

    return news  # 返回包含新闻标题和内容的字典列表
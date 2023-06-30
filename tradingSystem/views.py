from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from .utils import get_stock_comments
import akshare as ak
import pandas as pd
from .models import UserTable, StockInfo, HistoryTradeTable, StockComment, CommentReply, News
from .utils import get_top10, get_news, get_buy_in_out
from utils import getAstock, cram_news
from config.createUser import gen_photo_url, banks
from tradingSystem import models
from sqlalchemy import create_engine
import tushare as ts
import datetime
import pymysql
import numpy as np
import time
import uuid
import os

from utils import insertDayData, insertEverydayTicksData, datalasting


def goto_login(request):
    return render(request, 'login.html')


def mylogin(request):
    if request.POST:
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        message = ''
        try:
            adm = User.objects.get(username=phone_number)
            login(request, adm)
            user_num = UserTable.objects.count()
            stock_num = StockInfo.objects.count()
            request.session['user_name'] = phone_number
            request.session['username'] = adm.username
            request.session['online'] = True
            request.session['user_num'] = user_num
            request.session['stock_num'] = stock_num
            request.session['photo_url'] = '../static/img/head.jpg'
            request.session['phone_num'] = adm.username

            return redirect('tradingSystem:adm_index')
        except ObjectDoesNotExist:
            try:
                user = UserTable.objects.get(phone_number=phone_number)
                if user.password == password:
                    login(request, user)
                    request.session['user_name'] = user.user_name
                    request.session['photo_url'] = user.photo_url
                    print(user.photo_url)
                    request.session['user_id'] = user.user_id
                    request.session['user_email'] = user.user_email
                    request.session['account_num'] = user.account_num
                    request.session['account_type'] = user.account_type
                    request.session['account_balance'] = user.account_balance
                    request.session['id_no'] = user.id_no
                    request.session['phone_number'] = user.phone_number
                    return redirect('tradingSystem:index')
                else:
                    message = "您的密码错误"
            except ObjectDoesNotExist:
                message = "用户不存在"
    return render(request, 'login.html', locals())


def log_out(request):
    logout(request)
    request.session.flush()
    return redirect('tradingSystem:goto_login')


def index(request):
    try:
        if request.session['phone_number']:
            phone_number = request.session['phone_number']
            user = UserTable.objects.get(phone_number=phone_number)
            comments = StockComment.objects.filter(user_id=user)
            all_news = News.objects.all()
            page = request.GET.get('page', 1)
            paginator = Paginator(all_news, 8)
            if page > paginator.num_pages:
                page = 1
            news_list = get_news()
            top10stock = get_top10()
            context = {
                'top10stock': top10stock,
                'comments': comments,
                'user': user,
                'news_list': news_list,
                'page': page
            }
            return render(request, 'index.html', context)
        else:
            return redirect("tradingSystem:goto_login")
    except Exception:
        return redirect("tradingSystem:goto_login")


def change_news(request):
    news_list = cram_news.gen_news()[:8]
    return JsonResponse({"news_list": news_list})


def user_profile(request):
    try:

        if request.session['phone_number']:

            phone_number = request.session['phone_number']
            user = UserTable.objects.get(phone_number=phone_number)
            buy_in, buy_out = get_buy_in_out(phone_number)
            context = {
                'banks': banks,
                'user': user,
                'buy_in': buy_in,
                'buy_out': buy_out
            }
            return render(request, 'tradingSystem/user_profile.html', context)
        else:

            return redirect("tradingSystem:goto_login")
    except Exception:

        return redirect("tradingSystem:goto_login")


def deal_user_change(request):
    message = ""
    try:
        if request.POST:
            user_id = request.POST['user_id']
            user_name = request.POST['user_name']
            phone_number = request.POST['phone_number']
            user_sex = request.POST['user_sex']
            id_no = request.POST['id_no']
            user_email = request.POST['user_email']
            password = request.POST['password']
            conf_password = request.POST['conf_password']
            account_type = request.POST['account_type']
            account_number = request.POST['account_num']
            if conf_password != password:
                message = "确认密码不符"
            else:
                try:
                    user = UserTable.objects.get(user_id=user_id)
                    user.phone_number = phone_number
                    user.user_sex = user_sex
                    user.user_name = user_name
                    user.user_email = user_email
                    user.password = password
                    user.account_type = account_type
                    user.account_num = account_number
                    user.id_no = id_no
                    user.save()
                except Exception:
                    message = "修改信息失败，请仔细检查，或稍后重试"
    except Exception:
        message = "您的信息有误，请仔细检查"
    context = {
        'message': message,
        'banks': banks
    }
    return render(request, "tradingSystem/user_profile.html", context)


def stock_list(request):
    stockl = models.StockInfo.objects.all()
    stockt = stockl[0:100]

    context = {
        "stock": stockt
    }

    return render(request, 'stock_list.html', context)


def GetAKStockData(stock_id):
    today = time.strftime("%Y%m%d")
    begin = str((time.localtime().tm_year - 1) * 10000 + time.localtime().tm_mon * 100 + time.localtime().tm_mday)

    Data = ak.stock_zh_a_hist(symbol=stock_id, period="daily", start_date=begin, end_date=today, adjust="")[['日期', '开盘', '收盘', '最低', '最高']]
    Data['日期'] = pd.to_datetime(Data['日期'])
    Data['日期'] = Data['日期'].dt.strftime('%Y/%m/%d')
    Data.columns = ['date', 'open', 'close', 'lowest', 'highest']
    ans_tuple = tuple(Data.itertuples(index=False, name=None))
    return ans_tuple


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
    df = ak.stock_zh_a_spot_em()
    df = df[['代码', '昨收', '最新价', '涨跌幅']]
    df.columns = ['stock_id', 'closing_price_y', 'open_price_t', 'change_extent']

    pro = ts.pro_api(GetProApi())
    data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    data['suffix'] = data['ts_code'].str[-3:]
    data = data[data['suffix'].isin(['.SZ', '.SH'])]
    data['suffix'] = data['suffix'].replace({'.SZ': '深证', '.SH': '上证'})
    data = data[['symbol', 'name', 'list_date', 'suffix', 'industry']]
    data.columns = ['stock_id', 'stock_name', 'issuance_time', 'stock_type', 'block']

    Data = pd.merge(data, df, on='stock_id')
    Data = Data[['stock_id', 'stock_name', 'issuance_time', 'closing_price_y', 'open_price_t', 'stock_type', 'block', 'change_extent']]
    Data = Data.dropna()
    return Data


def RefreashStockInfo():
    engine = create_engine('mysql+pymysql://trading:trading_1@tradingsystem.mysql.polardb.rds.aliyuncs.com/stocktrading')

    with engine.begin() as connection:
        connection.execute('SET FOREIGN_KEY_CHECKS = 0')  # 禁用外键检查
        connection.execute('DELETE FROM stock_info')
        connection.execute('SET FOREIGN_KEY_CHECKS = 1')  # 启用外键检查

    Data = GetStockInfo()

    Data.to_sql('stock_info', con=engine, if_exists='append', index=False)


def stock_info(request, stock_id):
    comments = get_stock_comments(stock_id)

    choosenStock = models.StockInfo.objects.filter(stock_id=stock_id)
    hisData = np.array(GetAKStockData(stock_id)).tolist()
    if (choosenStock[0].stock_type == "上证"):
        hold_vol = getAstock.getAstock(stock_id + ".SH")
    else:
        hold_vol = getAstock.getAstock(stock_id + ".SZ")

    context = {
        "sid": choosenStock[0].stock_id,
        "sname": choosenStock[0].stock_name,
        "issuance_time": choosenStock[0].issuance_time,
        "closing_price_y": choosenStock[0].closing_price_y,
        "open_price_t": choosenStock[0].open_price_t,
        "stock_type": choosenStock[0].stock_type,
        "block": choosenStock[0].block,
        "change_extent": choosenStock[0].change_extent,
        "hold_vold": hold_vol,
        "hisData": hisData,
        'stock_id': stock_id,
        'comments': comments,
    }
    return render(request, 'stock_details.html', context)


def buy_in_stock(request):
    if request.is_ajax():
        if request.method == 'GET':
            price = float(request.GET.get("price"))
            shares = int(request.GET.get("shares"))
            s_id = request.GET.get("s_id")
            fare = price * shares

            buyer = models.UserTable.objects.filter(phone_number=request.session['phone_number'])

            stock_in = models.StockInfo.objects.filter(stock_id=s_id)
            money = 0
            if (buyer[0].account_balance >= fare and buyer[0].freeze == False and buyer[0].account_opened == True):
                money = 1
                models.UserTable.objects.filter(phone_number=request.session['phone_number']).update(
                    account_balance=buyer[0].account_balance - fare)
                option_stock = models.OptionalStockTable.objects.filter(user_id=buyer[0], stock_id=stock_in[0])
                if (len(option_stock) == 0):
                    models.OptionalStockTable.objects.create(
                        user_id=buyer[0],
                        stock_id=stock_in[0],
                        num_of_shares=shares
                    )
                else:
                    models.OptionalStockTable.objects.filter(user_id=buyer[0], stock_id=stock_in[0]).update(
                        num_of_shares=option_stock[0].num_of_shares + shares
                    )
                models.HistoryTradeTable.objects.create(
                    user_id=buyer[0],
                    stock_id=stock_in[0],
                    trade_price=price,
                    trade_shares=shares,
                    trade_time=time.strftime('%Y-%m-%d-%H:%M', time.localtime(time.time()))
                )
                return JsonResponse({"flag": 1, "money": money})
            else:
                if (buyer[0].account_balance >= fare):
                    money = 1
                else:
                    money = 0

                return JsonResponse({"flag": 0, "money": money})


def sold_stock(request):
    solder = models.UserTable.objects.filter(phone_number=request.session['phone_number'])
    stocks = models.OptionalStockTable.objects.filter(user_id=solder[0])  # 用户选股表

    pri = []
    for i in range(0, len(stocks)):
        pri.append({"price": ts.get_realtime_quotes(stocks[i].stock_id.stock_id)['price'][0], "obj": stocks[i]})
    context = {"stocks": pri}
    return render(request, 'sold_stock.html', context)


def out(request, stock_id):
    choosenStock = models.StockInfo.objects.filter(stock_id=stock_id)
    hisData = np.array(GetAKStockData(stock_id)).tolist()
    if (choosenStock[0].stock_type == "上证"):
        hold_vol = getAstock.getAstock(stock_id + ".SH")
    else:
        hold_vol = getAstock.getAstock(stock_id + ".SZ")
    stock = StockInfo.objects.get(stock_id=stock_id)
    comments = StockComment.objects.filter(stock_id=stock)
    context = {
        "sid": choosenStock[0].stock_id,
        "sname": choosenStock[0].stock_name,
        "issuance_time": choosenStock[0].issuance_time,
        "closing_price_y": choosenStock[0].closing_price_y,
        "open_price_t": choosenStock[0].open_price_t,
        "stock_type": choosenStock[0].stock_type,
        "block": choosenStock[0].block,
        "change_extent": choosenStock[0].change_extent,
        "hold_vold": hold_vol,
        "hisData": hisData,
        "comments": comments
    }
    return render(request, 'sold_out_stock.html', context)


def base(request):
    return render(request, 'base.html')


def register(request):
    return render(request, 'register.html')


def do_register(request):
    user_name = request.POST['user_name']
    phone_number = request.POST['phone_number']
    user_sex = request.POST['user_sex']
    id_no = request.POST['id_no']
    user_email = request.POST['user_email']
    password = request.POST['password']
    account_type = request.POST['account_type']
    account_number = request.POST['account_number']
    photo_url = gen_photo_url()
    message = ""
    try:
        user = UserTable.objects.create(
            user_name=user_name,
            user_email=user_email,
            user_sex=user_sex,
            user_id=str(uuid.uuid4())[:8],
            id_no=id_no,
            password=password,
            account_type=account_type,
            account_num=account_number,
            phone_number=phone_number,
            account_balance=0,
            photo_url=photo_url
        )
        user.save()
        print("success register user")
        print(user)
    except Exception:
        print(Exception)
        message = "注册失败，请检查或稍后再试！"
        return render(request, 'register.html', locals())
    return redirect('tradingSystem:goto_login')


def stockdetails(request):
    return render(request, 'stock_details.html')


def is_market_open():
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


def stock_list(request):
    if is_market_open():
        RefreashStockInfo()
    stockl = models.StockInfo.objects.all()

    context = {
        "stock": stockl
    }

    return render(request, 'stock_list.html', context)


def stock_comment(request):
    return render(request, 'stock_comments.html')


def sold_out_stock(request):
    if request.is_ajax():
        if request.method == 'GET':
            price = float(request.GET.get("price"))
            shares = int(request.GET.get("shares"))
            holdon = int(request.GET.get("holdon"))
            s_id = request.GET.get("s_id")

            solder = models.UserTable.objects.filter(phone_number=request.session['phone_number'])

            stock_sold = models.StockInfo.objects.filter(stock_id=s_id)
            money = 0
            if (holdon <= shares):
                models.UserTable.objects.filter(phone_number=request.session['phone_number']).update(
                    account_balance=solder[0].account_balance + holdon * price)
                models.HistoryTradeTable.objects.create(
                    user_id=solder[0],
                    stock_id=stock_sold[0],
                    trade_price=price,
                    trade_shares=0 - holdon,
                    trade_time=time.strftime('%Y-%m-%d-%H:%M', time.localtime(time.time()))
                )
                models.OptionalStockTable.objects.filter(user_id=solder[0], stock_id=stock_sold[0]).delete()
                return JsonResponse({"flag": 1, "rest": 0})
            else:
                models.UserTable.objects.filter(phone_number=request.session['phone_number']).update(
                    account_balance=solder[0].account_balance + shares * price)
                models.HistoryTradeTable.objects.create(
                    user_id=solder[0],
                    stock_id=stock_sold[0],
                    trade_price=price,
                    trade_shares=0 - shares,
                    trade_time=time.strftime('%Y-%m-%d-%H:%M', time.localtime(time.time()))
                )
                option_stock = models.OptionalStockTable.objects.filter(user_id=solder[0], stock_id=stock_sold[0])
                record = option_stock[0].num_of_shares - shares
                models.OptionalStockTable.objects.filter(user_id=solder[0], stock_id=stock_sold[0]).update(
                    num_of_shares=option_stock[0].num_of_shares - shares
                )
                return JsonResponse({"flag": 1, "rest": record})


def get_real_holdon(request):
    if request.is_ajax():
        if request.method == 'GET':
            sym = request.GET.get("id")
            solder = models.UserTable.objects.filter(phone_number=request.session['phone_number'])
            stock_sold = models.StockInfo.objects.filter(stock_id=sym)
            option_stock = models.OptionalStockTable.objects.filter(user_id=solder[0], stock_id=stock_sold[0])
            return JsonResponse({"holdon": option_stock[0].num_of_shares, "price": ts.get_realtime_quotes(symbols=sym)['price'][0]})


def stockdetails(request):
    return render(request, 'stock_details.html')


def add_stock_comment(request):
    user = UserTable.objects.get(phone_number=request.session.get('phone_number'))
    if request.POST:
        title = request.POST.get('comment_title')
        content = request.POST.get('comment_content')
        stock_id = request.POST.get('stock_id')
        print(title, content, stock_id)
        stock = StockInfo.objects.get(stock_id=stock_id)
        comment = StockComment.objects.create(user_id=user, stock_id=stock, title=title, content=content)
        comment.save()
        return redirect('tradingSystem:stock_info', stock_id=stock_id)


def comment_detail(request, comment_id):
    user = UserTable.objects.get(phone_number=request.session['phone_number'])
    comment = StockComment.objects.get(id=comment_id)
    replys = CommentReply.objects.filter(comment=comment)
    context = {
        'comment': comment,
        'replys': replys,
        'user': user
    }
    return render(request, 'comment_detail.html', context)


def add_reply(request):
    if request.POST:
        comment_id = request.POST.get('comment_id')
        phone_number = request.POST.get('phone_number')
        content = request.POST.get('content')
        comment = StockComment.objects.get(id=comment_id)
        user = UserTable.objects.get(phone_number=phone_number)
        reply = CommentReply.objects.create(
            user_id=user,
            comment=comment,
            content=content
        )
        # reply.save()
        return redirect('tradingSystem:comment_detail', comment_id=comment_id)


def get_real_quotes(request):
    if request.is_ajax():
        if request.method == 'GET':
            sym = request.GET.get("id")

            df = ts.get_realtime_quotes(symbols=sym)
            df = df[['code', 'name', 'price', 'bid', 'ask', 'volume', 'amount', 'time']]

            res = np.array(df)
            res = res[:, [2]]

            return JsonResponse({"price": res[0][0]})


def view_user_profile(request, phone_number):
    user = UserTable.objects.get(phone_number=phone_number)
    buy_in, buy_out = get_buy_in_out(phone_number)
    context = {
        'user': user,
        'buy_in': buy_in,
        'buy_out': buy_out
    }
    return render(request, 'view_user_profile.html', context)


def news_detail(request, news_id):
    user = UserTable.objects.get(phone_number=request.session['phone_number'])

    news = News.objects.get(id=news_id)
    nx_news = news_id + 1
    pre_news = news_id - 1

    while not News.objects.filter(id=nx_news).exists():
        nx_news += 1
    while not News.objects.filter(id=pre_news).exists():
        pre_news -= 1

    context = {
        'user': user,
        'news': news,
        'nx_news': nx_news,
        'pre_news': pre_news
    }
    return render(request, 'news_detail.html', context)


def update_img(request):
    if request.method == 'POST':
        user = UserTable.objects.get(phone_number=request.session['phone_number'])
        my_file = request.FILES.get('teamFile', None)
        message = ""
        filename = os.path.splitext(my_file._name)[1]
        save_name = 'static/img/' + user.phone_number + filename
        code = 1000
        if my_file:
            with open(save_name, 'wb') as file:
                file.write(my_file.read())
            code = 0
            user.photo_url = '/' + save_name
            user.save()
            print("修改成功呢")
        else:
            filename = ''
            message = "修改失败，请稍后再试！"
        context = {
            'message': message,
            'banks': banks,
            "code": code, "msg": {"url": '../static/img/%s' % (filename), 'filename': my_file._name}
        }
        return JsonResponse(context)


def comment_list(request):
    try:
        user = UserTable.objects.get(phone_number=request.session['phone_number'])
        comments = StockComment.objects.filter(user_id=user)
        results = []
        for comment in comments:
            results.append({
                'stock_id': comment.stock_id.stock_id,
                'comment_id': comment.id,
                'stock_name': comment.stock_id.stock_name,
                'title': comment.title,
                'content': comment.content,
                'comment_time': comment.comment_time,
                'reply_nums': CommentReply.objects.filter(comment=comment).count(),
            })
        context = {
            'results': results,
            'user': user,
        }
        return render(request, 'comment_list.html', context)
    except:
        return redirect('tradingSystem:mylogin')


def comment_delete(request, comment_id):
    comment = StockComment.objects.get(id=comment_id)
    comment.delete()
    return redirect('tradingSystem:comment_list')


def uphold(request):
    top10stock = get_top10
    user_num = UserTable.objects.count()
    stock_num = StockInfo.objects.count()
    comment_num = StockComment.objects.count()
    trading_num = HistoryTradeTable.objects.count()
    news_list = get_news()
    context = {
        'top10stock': top10stock,
        'user_num': user_num,
        'stock_num': stock_num,
        'comment_num': comment_num,
        'trading_num': trading_num,
        'news_list': news_list
    }
    return render(request, 'uphold.html', context)


def updateEveDayOC(request):  # 对stockinfo更新每支股票最新收盘价开盘价
    if request.is_ajax():
        if request.method == 'GET':
            datalasting.getTscode()
            return JsonResponse({"flag": 1})


def updateDayData(request):  # 对每张股票表加上当天的数据
    if request.is_ajax():
        if request.method == 'GET':
            insertDayData.upHold()
            return JsonResponse({"flag": 1})


def updateTickData(request):  # 每天开盘时开启线程检测3754支股票的实时数据，并且添加进表中
    if request.is_ajax():
        if request.method == 'GET':
            insertEverydayTicksData.getTodayRealTimeData()
            return JsonResponse({"flag": 1})

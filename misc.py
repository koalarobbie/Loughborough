# -*- coding: utf-8 -*-
from datetime import datetime
import tushare as ts



def orderid2traderid(id:str)->int: 
    if id.startswith('20') and len(id) > 15:
        return int(id[8:])
    return int(id)

def traderid2orderid(id:str)->str:
    return    datetime.now().strftime("%Y%m%d") + str(id)
    

def get_current_ma30(code:str)->float:
    today = datetime.now().strftime("%Y%m%d")
    ts.set_token('0f790573e7e4ed18eb1d16d09b26d33bee3ab687b83b844432e3ef2e')
    pro = ts.pro_api()
    df = pro.daily(ts_code=code, start_date='20260101', end_date=today)
    if df is not None and len(df) > 30:
        ma30  =  round(df['close'][:30].mean(),2)
        return ma30
    return -1


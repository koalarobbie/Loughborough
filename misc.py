# -*- coding: utf-8 -*-
from datetime import datetime


def orderid2traderid(id:str)->int: 
    if id.startswith('20') and len(id) > 15:
        return int(id[8:])
    return int(id)

def traderid2orderid(id:str)->str:
    return    datetime.now().strftime("%Y%m%d") + str(id)
    
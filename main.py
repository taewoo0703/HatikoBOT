# version 0.0.4
from fastapi.exception_handlers import (
    request_validation_exception_handler,
)

from fastapi import FastAPI, Request, status, BackgroundTasks
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
import httpx
from exchange.stock.kis import KoreaInvestment
from model import MarketOrder, PriceRequest
from utility import settings, log_order_message, log_alert_message, print_alert_message, logger_test, log_order_error_message, log_validation_error_message, log_recv_message
import traceback
from exchange import get_exchange, log_message, db, settings


app = FastAPI(default_response_class=ORJSONResponse)


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    db.close()

whitelist = ["52.89.214.238", "34.212.75.30",
             "54.218.53.128", "52.32.178.7", "127.0.0.1"]
whitelist = whitelist + settings.WHITELIST


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.perf_counter()
#     response = await call_next(request)
#     process_time = time.perf_counter() - start_time
#     response.headers["X-Process-Time"] = str(process_time)
#     return response


@app.middleware('http')
async def settings_whitelist_middleware(request: Request, call_next):
    if request.client.host not in whitelist:
        msg = f"{request.client.host}는 안됩니다"
        print(msg)
        return ORJSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=f"{request.client.host} Not Allowed")
    response = await call_next(request)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    msgs = [f"[에러{index+1}] " + f"{error.get('msg')} \n{error.get('loc')}"
            for index, error in enumerate(exc.errors())]
    message = "[Error]\n"
    for msg in msgs:
        message = message+msg+"\n"

    log_validation_error_message(f"{message}\n {exc.body}")
    return await request_validation_exception_handler(request, exc)


@app.get("/ip")
async def get_ip():
    data = httpx.get("https://ifconfig.me").text
    log_message(data)
    return data


@ app.get("/hi")
async def welcome():
    return "hi!!"


@ app.post("/price")
async def price(price_req: PriceRequest, background_tasks: BackgroundTasks):
    exchange = get_exchange(price_req.exchange)
    price = exchange.dict()[price_req.exchange].fetch_price(price_req.base, price_req.quote)
    return price


def log(exchange_name, result, order_info):
    log_order_message(exchange_name, result, order_info)
    print_alert_message(order_info)

# HatikoBOT에서 추가한 영역 by PTW 20230116
isExistLong1 = False
isExistLong2 = False
isExistLong3 = False
isExistLong4 = False
isExistShort1 = False
isExistShort2 = False
isExistShort3 = False
isExistShort4 = False
baseLong1 = ""
baseLong2 = ""
baseLong3 = ""
baseLong4 = ""
baseShort1 = ""
baseShort2 = ""
baseShort3 = ""
baseShort4 = ""
nMaxTry = 10

#Hatiko4를 위한 변수들 20230206
baseLong1_list = []
baseLong2_list = []
baseLong3_list = []
baseLong4_list = []
baseShort1_list = []
baseShort2_list = []
baseShort3_list = []
baseShort4_list = []


@app.get("/version")
async def version():
    return "2023-04-01 version. 트뷰 내 바이낸스 선물티커 변경 반영"

@ app.get("/hatikoinfo")
async def hatikoinfo():
    res = {
        "isExistLong1" : isExistLong1,
        "isExistLong2" : isExistLong2,
        "isExistLong3" : isExistLong3,
        "isExistLong4" : isExistLong4,
        "isExistShort1" : isExistShort1,
        "isExistShort2" : isExistShort2,
        "isExistShort3" : isExistShort3,
        "isExistShort4" : isExistShort4,
        "baseLong1" : baseLong1,
        "baseLong2" : baseLong2,
        "baseLong3" : baseLong3,
        "baseLong4" : baseLong4,
        "baseShort1" : baseShort1,
        "baseShort2" : baseShort2,
        "baseShort3" : baseShort3,
        "baseShort4" : baseShort4,
        }
    return res

@ app.get("/hatiko4info")
async def hatiko4info():
    res = {
        "baseLong1_list"  : str(baseLong1_list), 
        "baseLong2_list"  : str(baseLong2_list), 
        "baseLong3_list"  : str(baseLong3_list), 
        "baseLong4_list"  : str(baseLong4_list), 
        "baseShort1_list" : str(baseShort1_list),
        "baseShort2_list" : str(baseShort2_list),
        "baseShort3_list" : str(baseShort3_list),
        "baseShort4_list" : str(baseShort4_list)
        }
    return res



@ app.post("/hatiko")
async def hatiko(order_info: MarketOrder, background_tasks: BackgroundTasks):
    global isExistLong1, isExistLong2, isExistLong3, isExistLong4
    global isExistShort1, isExistShort2, isExistShort3, isExistShort4
    global baseLong1, baseLong2, baseLong3, baseLong4
    global baseShort1, baseShort2, baseShort3, baseShort4
    global nMaxTry
    # 초기화 단계
    result = None
    nGoal = 0
    nComplete = 0

    # [Debug] 트뷰 시그널이 도착했다는 알람 발생
    background_tasks.add_task(log_recv_message, order_info)

    # nMaxTry 횟수만큼 자동매매 시도
    for nTry in range(nMaxTry):
        if nGoal != 0 and nComplete == nGoal:   # 이미 매매를 성공하면 더이상의 Try를 생략함.
            break

        try:
            # 엔트리 주문 중복 무시
            if isExistLong1 and order_info.order_name == "Long1":
                return {"result" : "ignore"}
            if isExistLong2 and order_info.order_name == "Long2":
                return {"result" : "ignore"}
            if isExistLong3 and order_info.order_name == "Long3":
                return {"result" : "ignore"}
            if isExistLong4 and order_info.order_name == "Long4":
                return {"result" : "ignore"}
            if isExistShort1 and order_info.order_name == "Short1":
                return {"result" : "ignore"}
            if isExistShort2 and order_info.order_name == "Short2":
                return {"result" : "ignore"}
            if isExistShort3 and order_info.order_name == "Short3":
                return {"result" : "ignore"}
            if isExistShort4 and order_info.order_name == "Short4":
                return {"result" : "ignore"}
            
            # 안 산 주문에 대한 종료 무시
            if order_info.side.startswith("close/"):
                if order_info.base not in [baseLong1, baseLong2, baseLong3, baseLong4, baseShort1, baseShort2, baseShort3, baseShort4]:
                    return {"result" : "ignore"}
                if order_info.order_name in ["TakeProfitS2", "TakeProfitS3", "TakeProfitS4", "TakeProfitL2", "TakeProfitL3", "TakeProfitL4"]:
                    return {"result" : "ignore"}

            exchange_name = order_info.exchange.upper()
            exchange = get_exchange(exchange_name, order_info.kis_number)
            if exchange_name in ("BINANCE"):    # Binance Only
                bot = exchange.dict()[order_info.exchange]
                bot.order_info = order_info
                if order_info.side.startswith("entry/"):
                    if order_info.stop_price and order_info.profit_price:
                        pass
                    else:
                        ###################################
                        # Entry 매매 코드
                        ###################################
                        
                        if nTry == 0:   # 초기 세팅
                            symbol = bot.parse_symbol(order_info.base, order_info.quote)
                            side = bot.parse_side(order_info.side)
                            quote = bot.parse_quote(order_info.quote)
                            if order_info.leverage is not None:
                                bot.future.set_leverage(order_info.leverage, symbol)
                            # total amount를 max_amount로 쪼개기
                            total_amount = bot.get_amount(order_info.base, quote, order_info.amount, order_info.percent)
                            max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                            min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"] 
                            # Set nGoal
                            entry_amount_list = []
                            if (total_amount % max_amount < min_amount):
                                nGoal = total_amount // max_amount
                                for i in range(int(nGoal)):
                                    entry_amount_list.append(max_amount)
                            else:
                                nGoal = total_amount // max_amount + 1
                                for i in range(int(nGoal - 1)):
                                    entry_amount_list.append(max_amount)
                                entry_amount_list.append(total_amount % max_amount)
                            # 시장가를 지정가로 변환
                            # 슬리피지 0.8프로 짜리 지정가로 변환
                            # 트뷰 시그널 가격과 1%의 괴리가 있으면 시그널 무시
                            current_price = bot.fetch_price(order_info.base, quote)
                            if order_info.order_name in ["Long1", "Long2", "Long3", "Long4"] and current_price > order_info.price * 1.01:
                                return {"result" : "ignore"}
                            if order_info.order_name in ["Short1", "Short2", "Short3", "Short4"] and current_price < order_info.price * 0.99:
                                return {"result" : "ignore"}
                            slipage = 0.8
                            if side == "buy":
                                entry_price = current_price * (1 + slipage / 100)
                            if side == "sell":
                                entry_price = current_price * (1 - slipage / 100) 
                            
                        # 매매 주문
                        for i in range(int(nGoal-nComplete)):
                            entry_amount = entry_amount_list[nComplete]
                            result = bot.future.create_order(symbol, "limit", side, abs(entry_amount), entry_price)
                            nComplete += 1
                            # 디스코드 로그생성
                            background_tasks.add_task(log, exchange_name, result, order_info)
                        
                        # 매매가 전부 종료되면
                        # hatikoinfo 업데이트
                        if order_info.order_name == "Long1":
                            isExistLong1 = True
                            baseLong1 = order_info.base
                        if order_info.order_name == "Long2":
                            isExistLong2 = True
                            baseLong2 = order_info.base                
                        if order_info.order_name == "Long3":
                            isExistLong3 = True
                            baseLong3 = order_info.base
                        if order_info.order_name == "Long4":
                            isExistLong4 = True
                            baseLong4 = order_info.base
                        if order_info.order_name == "Short1":
                            isExistShort1 = True
                            baseShort1 = order_info.base                
                        if order_info.order_name == "Short2":
                            isExistShort2 = True
                            baseShort2 = order_info.base
                        if order_info.order_name == "Short3":
                            isExistShort3 = True
                            baseShort3 = order_info.base
                        if order_info.order_name == "Short4":
                            isExistShort4 = True
                            baseShort4 = order_info.base


                if order_info.side.startswith("close/"):
                    # result = bot.market_close(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent)

                    #############################
                    ## Close 매매코드
                    #############################
                    if nTry == 0:   # 초기 세팅
                        symbol = bot.parse_symbol(order_info.base, order_info.quote)
                        side = bot.parse_side(order_info.side)
                        quote = bot.parse_quote(order_info.quote)
                        
                        # total amount를 max_amount로 쪼개기
                        total_amount = bot.get_amount(order_info.base, quote, order_info.amount, order_info.percent)
                        max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                        min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"]
                        # Set nGoal
                        close_amount_list = []
                        if (total_amount % max_amount < min_amount):
                            nGoal = total_amount // max_amount
                            for i in range(int(nGoal)):
                                close_amount_list.append(max_amount)
                        else:
                            nGoal = total_amount // max_amount + 1
                            for i in range(int(nGoal - 1)):
                                close_amount_list.append(max_amount)
                            close_amount_list.append(total_amount % max_amount)
                        # 트뷰에 나오는 청산 가격에 그대로 청산
                        close_price = order_info.price
                    
                    # 매매 주문
                    for i in range(int(nGoal-nComplete)):
                        close_amount = close_amount_list[nComplete]
                        result = bot.future.create_order(symbol, "limit", side, close_amount, close_price, params={"reduceOnly": True})
                        nComplete += 1
                        background_tasks.add_task(log, exchange_name, result, order_info)

                    # 매매가 전부 종료된 후
                    # 어떤 베이스인지 찾아서 isExist를 False로 바꿔줘야함
                    if order_info.base == baseLong1:
                        isExistLong1 = False
                        baseLong1 = ""
                    if order_info.base == baseLong2:
                        isExistLong2 = False                
                        baseLong2 = ""
                    if order_info.base == baseLong3:
                        isExistLong3 = False
                        baseLong3 = ""
                    if order_info.base == baseLong4:
                        isExistLong4 = False
                        baseLong4 = ""
                    if order_info.base == baseShort1:
                        isExistShort1 = False
                        baseShort1 = ""
                    if order_info.base == baseShort2:
                        isExistShort2 = False
                        baseShort2 = ""
                    if order_info.base == baseShort3:
                        isExistShort3 = False
                        baseShort3 = ""
                    if order_info.base == baseShort4:
                        isExistShort4 = False      
                        baseShort4 = ""

        except TypeError:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
        except Exception:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
            log_alert_message(order_info)

        else:
            return {"result": "success"}

        finally:
            pass

@ app.post("/hatiko4")
async def hatiko4(order_info: MarketOrder, background_tasks: BackgroundTasks):
    """
    /hatiko의 분산투자 버전
    Long 시그널은 4 종목까지 분산투자를 하고, Short 시그널은 단일 몰빵투자를 한다.
    [기존 /hatiko 대비 변경내역]
    1. 매수종목을 리스트로 관리함. 리스트에 최대개수 이상 들어오는 시그널은 무시. 혹시 같은 종목에서 Long1 시그널 중복 발생시 후속타 무시
    2. bot.get_amount() 대신 bot.get_amount_hatiko4()를 씀. 트뷰와 무관하게 그냥 전체 자금 기준 16분할하는 방식으로 매매 수량을 정함.(청산당할MDD보정 포함되어 있음)
    """
    global baseLong1_list, baseLong2_list, baseLong3_list, baseLong4_list
    global baseShort1_list, baseShort2_list, baseShort3_list, baseShort4_list
    global nMaxTry

    # hatiko4 상수
    nMaxLong = 4    # 최대 4종목 분산투자
    nMaxShort = 1   # 최대 1종목 몰빵투자

    # 초기화 단계
    result = None
    nGoal = 0
    nComplete = 0

    # [Debug] 트뷰 시그널이 도착했다는 알람 발생
    background_tasks.add_task(log_recv_message, order_info)

    # nMaxTry 횟수만큼 자동매매 시도
    for nTry in range(nMaxTry):
        if nGoal != 0 and nComplete == nGoal:   # 이미 매매를 성공하면 더이상의 Try를 생략함.
            break

        try:
            # 엔트리 주문 중복 무시
            if (len(baseLong1_list) >= nMaxLong or order_info.base in baseLong1_list) and order_info.order_name == "Long1":
                return {"result" : "ignore"}
            if (len(baseLong2_list) >= nMaxLong or order_info.base in baseLong2_list) and order_info.order_name == "Long2":
                return {"result" : "ignore"}
            if (len(baseLong3_list) >= nMaxLong or order_info.base in baseLong3_list) and order_info.order_name == "Long3":
                return {"result" : "ignore"}
            if (len(baseLong4_list) >= nMaxLong or order_info.base in baseLong4_list) and order_info.order_name == "Long4":
                return {"result" : "ignore"}
            if (len(baseShort1_list) >= nMaxShort or order_info.base in baseShort1_list) and order_info.order_name == "Short1":
                return {"result" : "ignore"}
            if (len(baseShort2_list) >= nMaxShort or order_info.base in baseShort2_list) and order_info.order_name == "Short2":
                return {"result" : "ignore"}
            if (len(baseShort3_list) >= nMaxShort or order_info.base in baseShort3_list) and order_info.order_name == "Short3":
                return {"result" : "ignore"}
            if (len(baseShort4_list) >= nMaxShort or order_info.base in baseShort4_list) and order_info.order_name == "Short4":
                return {"result" : "ignore"}
            
            # 안 산 주문에 대한 종료 무시
            if order_info.side.startswith("close/"):
                if order_info.base not in (baseLong1_list + baseLong2_list + baseLong3_list + baseLong4_list + baseShort1_list + baseShort2_list + baseShort3_list + baseShort4_list):
                    return {"result" : "ignore"}
                if order_info.order_name in ["TakeProfitS2", "TakeProfitS3", "TakeProfitS4", "TakeProfitL2", "TakeProfitL3", "TakeProfitL4"]:
                    return {"result" : "ignore"}

            exchange_name = order_info.exchange.upper()
            exchange = get_exchange(exchange_name, order_info.kis_number)
            if exchange_name in ("BINANCE"):    # Binance Only
                bot = exchange.dict()[order_info.exchange]
                bot.order_info = order_info
                if order_info.side.startswith("entry/"):
                    if order_info.stop_price and order_info.profit_price:
                        pass
                    else:
                        ###################################
                        # Entry 매매 코드
                        ###################################
                        
                        if nTry == 0:   # 초기 세팅
                            symbol = bot.parse_symbol(order_info.base, order_info.quote)
                            side = bot.parse_side(order_info.side)
                            quote = bot.parse_quote(order_info.quote)
                            if order_info.leverage is not None:
                                bot.future.set_leverage(order_info.leverage, symbol)
                            # total amount를 max_amount로 쪼개기
                            total_amount = bot.get_amount_hatiko4(order_info.base, quote)
                            max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                            min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"] 
                            # Set nGoal
                            entry_amount_list = []
                            if (total_amount % max_amount < min_amount):
                                nGoal = total_amount // max_amount
                                for i in range(int(nGoal)):
                                    entry_amount_list.append(max_amount)
                            else:
                                nGoal = total_amount // max_amount + 1
                                for i in range(int(nGoal - 1)):
                                    entry_amount_list.append(max_amount)
                                entry_amount_list.append(total_amount % max_amount)
                            # 시장가를 지정가로 변환
                            # 슬리피지 0.8프로 짜리 지정가로 변환
                            # 트뷰 시그널 가격과 1%의 괴리가 있으면 시그널 무시
                            current_price = bot.fetch_price(order_info.base, quote)
                            if order_info.order_name in ["Long1", "Long2", "Long3", "Long4"] and current_price > order_info.price * 1.01:
                                return {"result" : "ignore"}
                            if order_info.order_name in ["Short1", "Short2", "Short3", "Short4"] and current_price < order_info.price * 0.99:
                                return {"result" : "ignore"}
                            slipage = 0.8
                            if side == "buy":
                                entry_price = current_price * (1 + slipage / 100)
                            if side == "sell":
                                entry_price = current_price * (1 - slipage / 100) 
                            
                        # 매매 주문
                        for i in range(int(nGoal-nComplete)):
                            entry_amount = entry_amount_list[nComplete]
                            result = bot.future.create_order(symbol, "limit", side, abs(entry_amount), entry_price)
                            nComplete += 1
                            # 디스코드 로그생성
                            background_tasks.add_task(log, exchange_name, result, order_info)
                        
                        # 매매가 전부 종료되면
                        # 매매종목 리스트 업데이트
                        if order_info.order_name == "Long1":
                            baseLong1_list.append(order_info.base)
                        if order_info.order_name == "Long2":
                            baseLong2_list.append(order_info.base)  
                        if order_info.order_name == "Long3":
                            baseLong3_list.append(order_info.base)
                        if order_info.order_name == "Long4":
                            baseLong4_list.append(order_info.base)
                        if order_info.order_name == "Short1":
                            baseShort1_list.append(order_info.base)
                        if order_info.order_name == "Short2":
                            baseShort2_list.append(order_info.base)
                        if order_info.order_name == "Short3":
                            baseShort3_list.append(order_info.base)
                        if order_info.order_name == "Short4":
                            baseShort4_list.append(order_info.base)


                if order_info.side.startswith("close/"):
                    # result = bot.market_close(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent)

                    #############################
                    ## Close 매매코드
                    #############################
                    if nTry == 0:   # 초기 세팅
                        symbol = bot.parse_symbol(order_info.base, order_info.quote)
                        side = bot.parse_side(order_info.side)
                        quote = bot.parse_quote(order_info.quote)
                        
                        # total amount를 max_amount로 쪼개기
                        total_amount = bot.get_amount_hatiko4(order_info.base, quote)
                        max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                        min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"]
                        # Set nGoal
                        close_amount_list = []
                        if (total_amount % max_amount < min_amount):
                            nGoal = total_amount // max_amount
                            for i in range(int(nGoal)):
                                close_amount_list.append(max_amount)
                        else:
                            nGoal = total_amount // max_amount + 1
                            for i in range(int(nGoal - 1)):
                                close_amount_list.append(max_amount)
                            close_amount_list.append(total_amount % max_amount)
                        # 트뷰에 나오는 청산 가격에 그대로 청산
                        close_price = order_info.price
                    
                    # 매매 주문
                    for i in range(int(nGoal-nComplete)):
                        close_amount = close_amount_list[nComplete]
                        result = bot.future.create_order(symbol, "limit", side, close_amount, close_price, params={"reduceOnly": True})
                        nComplete += 1
                        background_tasks.add_task(log, exchange_name, result, order_info)

                    # 매매가 전부 종료된 후
                    # 매매종목 리스트 업데이트
                    if order_info.base in baseLong1_list:
                        baseLong1_list.remove(order_info.base)
                    if order_info.base in baseLong2_list:
                        baseLong2_list.remove(order_info.base)
                    if order_info.base in baseLong3_list:
                        baseLong3_list.remove(order_info.base)
                    if order_info.base in baseLong4_list:
                        baseLong4_list.remove(order_info.base)
                    if order_info.base in baseShort1_list:
                        baseShort1_list.remove(order_info.base)
                    if order_info.base in baseShort2_list:
                        baseShort2_list.remove(order_info.base)
                    if order_info.base in baseShort3_list:
                        baseShort3_list.remove(order_info.base)           
                    if order_info.base in baseShort4_list:
                        baseShort4_list.remove(order_info.base)

        except TypeError:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
        except Exception:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
            log_alert_message(order_info)

        else:
            return {"result": "success"}

        finally:
            pass

@ app.post("/hatiko1")
async def hatiko1(order_info: MarketOrder, background_tasks: BackgroundTasks):
    """
    기존 /hatiko와 동일한 로직.
    [기존 /hatiko 대비 변경내역]
    1. 매수종목을 리스트로 관리함. 리스트에 최대개수 이상 들어오는 시그널은 무시. 혹시 같은 종목에서 Long1 시그널 중복 발생시 후속타 무시
    2. 매매 비율 정할 때 전체 자금 4분할 하는걸로 정함.(hatiko4, hatiko2방식)
    """
    global baseLong1_list, baseLong2_list, baseLong3_list, baseLong4_list
    global baseShort1_list, baseShort2_list, baseShort3_list, baseShort4_list
    global nMaxTry

    # hatiko4 상수
    nMaxLong = 1    # 최대 1종목 몰빵투자
    nMaxShort = 1   # 최대 1종목 몰빵투자

    # 초기화 단계
    result = None
    nGoal = 0
    nComplete = 0

    # [Debug] 트뷰 시그널이 도착했다는 알람 발생
    background_tasks.add_task(log_recv_message, order_info)

    # nMaxTry 횟수만큼 자동매매 시도
    for nTry in range(nMaxTry):
        if nGoal != 0 and nComplete == nGoal:   # 이미 매매를 성공하면 더이상의 Try를 생략함.
            break

        try:
            # 엔트리 주문 중복 무시
            if (len(baseLong1_list) >= nMaxLong or order_info.base in baseLong1_list) and order_info.order_name == "Long1":
                return {"result" : "ignore"}
            if (len(baseLong2_list) >= nMaxLong or order_info.base in baseLong2_list) and order_info.order_name == "Long2":
                return {"result" : "ignore"}
            if (len(baseLong3_list) >= nMaxLong or order_info.base in baseLong3_list) and order_info.order_name == "Long3":
                return {"result" : "ignore"}
            if (len(baseLong4_list) >= nMaxLong or order_info.base in baseLong4_list) and order_info.order_name == "Long4":
                return {"result" : "ignore"}
            if (len(baseShort1_list) >= nMaxShort or order_info.base in baseShort1_list) and order_info.order_name == "Short1":
                return {"result" : "ignore"}
            if (len(baseShort2_list) >= nMaxShort or order_info.base in baseShort2_list) and order_info.order_name == "Short2":
                return {"result" : "ignore"}
            if (len(baseShort3_list) >= nMaxShort or order_info.base in baseShort3_list) and order_info.order_name == "Short3":
                return {"result" : "ignore"}
            if (len(baseShort4_list) >= nMaxShort or order_info.base in baseShort4_list) and order_info.order_name == "Short4":
                return {"result" : "ignore"}
            
            # 안 산 주문에 대한 종료 무시
            if order_info.side.startswith("close/"):
                if order_info.base not in (baseLong1_list + baseLong2_list + baseLong3_list + baseLong4_list + baseShort1_list + baseShort2_list + baseShort3_list + baseShort4_list):
                    return {"result" : "ignore"}
                if order_info.order_name in ["TakeProfitS2", "TakeProfitS3", "TakeProfitS4", "TakeProfitL2", "TakeProfitL3", "TakeProfitL4"]:
                    return {"result" : "ignore"}

            exchange_name = order_info.exchange.upper()
            exchange = get_exchange(exchange_name, order_info.kis_number)
            if exchange_name in ("BINANCE"):    # Binance Only
                bot = exchange.dict()[order_info.exchange]
                bot.order_info = order_info
                if order_info.side.startswith("entry/"):
                    if order_info.stop_price and order_info.profit_price:
                        pass
                    else:
                        ###################################
                        # Entry 매매 코드
                        ###################################
                        
                        if nTry == 0:   # 초기 세팅
                            symbol = bot.parse_symbol(order_info.base, order_info.quote)
                            side = bot.parse_side(order_info.side)
                            quote = bot.parse_quote(order_info.quote)
                            if order_info.leverage is not None:
                                bot.future.set_leverage(order_info.leverage, symbol)
                            # total amount를 max_amount로 쪼개기
                            total_amount = bot.get_amount_hatiko1(order_info.base, quote)
                            max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                            min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"] 
                            # Set nGoal
                            entry_amount_list = []
                            if (total_amount % max_amount < min_amount):
                                nGoal = total_amount // max_amount
                                for i in range(int(nGoal)):
                                    entry_amount_list.append(max_amount)
                            else:
                                nGoal = total_amount // max_amount + 1
                                for i in range(int(nGoal - 1)):
                                    entry_amount_list.append(max_amount)
                                entry_amount_list.append(total_amount % max_amount)
                            # 시장가를 지정가로 변환
                            # 슬리피지 0.8프로 짜리 지정가로 변환
                            # 트뷰 시그널 가격과 1%의 괴리가 있으면 시그널 무시
                            current_price = bot.fetch_price(order_info.base, quote)
                            if order_info.order_name in ["Long1", "Long2", "Long3", "Long4"] and current_price > order_info.price * 1.01:
                                return {"result" : "ignore"}
                            if order_info.order_name in ["Short1", "Short2", "Short3", "Short4"] and current_price < order_info.price * 0.99:
                                return {"result" : "ignore"}
                            slipage = 0.8
                            if side == "buy":
                                entry_price = current_price * (1 + slipage / 100)
                            if side == "sell":
                                entry_price = current_price * (1 - slipage / 100) 
                            
                        # 매매 주문
                        for i in range(int(nGoal-nComplete)):
                            entry_amount = entry_amount_list[nComplete]
                            result = bot.future.create_order(symbol, "limit", side, abs(entry_amount), entry_price)
                            nComplete += 1
                            # 디스코드 로그생성
                            background_tasks.add_task(log, exchange_name, result, order_info)
                        
                        # 매매가 전부 종료되면
                        # 매매종목 리스트 업데이트
                        if order_info.order_name == "Long1":
                            baseLong1_list.append(order_info.base)
                        if order_info.order_name == "Long2":
                            baseLong2_list.append(order_info.base)  
                        if order_info.order_name == "Long3":
                            baseLong3_list.append(order_info.base)
                        if order_info.order_name == "Long4":
                            baseLong4_list.append(order_info.base)
                        if order_info.order_name == "Short1":
                            baseShort1_list.append(order_info.base)
                        if order_info.order_name == "Short2":
                            baseShort2_list.append(order_info.base)
                        if order_info.order_name == "Short3":
                            baseShort3_list.append(order_info.base)
                        if order_info.order_name == "Short4":
                            baseShort4_list.append(order_info.base)


                if order_info.side.startswith("close/"):
                    # result = bot.market_close(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent)

                    #############################
                    ## Close 매매코드
                    #############################
                    if nTry == 0:   # 초기 세팅
                        symbol = bot.parse_symbol(order_info.base, order_info.quote)
                        side = bot.parse_side(order_info.side)
                        quote = bot.parse_quote(order_info.quote)
                        
                        # total amount를 max_amount로 쪼개기
                        total_amount = bot.get_amount_hatiko1(order_info.base, quote)
                        max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                        min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"]
                        # Set nGoal
                        close_amount_list = []
                        if (total_amount % max_amount < min_amount):
                            nGoal = total_amount // max_amount
                            for i in range(int(nGoal)):
                                close_amount_list.append(max_amount)
                        else:
                            nGoal = total_amount // max_amount + 1
                            for i in range(int(nGoal - 1)):
                                close_amount_list.append(max_amount)
                            close_amount_list.append(total_amount % max_amount)
                        # 트뷰에 나오는 청산 가격에 그대로 청산
                        close_price = order_info.price
                    
                    # 매매 주문
                    for i in range(int(nGoal-nComplete)):
                        close_amount = close_amount_list[nComplete]
                        result = bot.future.create_order(symbol, "limit", side, close_amount, close_price, params={"reduceOnly": True})
                        nComplete += 1
                        background_tasks.add_task(log, exchange_name, result, order_info)

                    # 매매가 전부 종료된 후
                    # 매매종목 리스트 업데이트
                    if order_info.base in baseLong1_list:
                        baseLong1_list.remove(order_info.base)
                    if order_info.base in baseLong2_list:
                        baseLong2_list.remove(order_info.base)
                    if order_info.base in baseLong3_list:
                        baseLong3_list.remove(order_info.base)
                    if order_info.base in baseLong4_list:
                        baseLong4_list.remove(order_info.base)
                    if order_info.base in baseShort1_list:
                        baseShort1_list.remove(order_info.base)
                    if order_info.base in baseShort2_list:
                        baseShort2_list.remove(order_info.base)
                    if order_info.base in baseShort3_list:
                        baseShort3_list.remove(order_info.base)           
                    if order_info.base in baseShort4_list:
                        baseShort4_list.remove(order_info.base)

        except TypeError:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
        except Exception:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
            log_alert_message(order_info)

        else:
            return {"result": "success"}

        finally:
            pass

@ app.post("/hatiko2")
async def hatiko2(order_info: MarketOrder, background_tasks: BackgroundTasks):
    """
    /hatiko의 분산투자 버전
    Long 시그널은 2 종목까지 분산투자를 하고, Short 시그널은 단일 몰빵투자를 한다.
    [기존 /hatiko 대비 변경내역]
    1. 매수종목을 리스트로 관리함. 리스트에 최대개수 이상 들어오는 시그널은 무시. 혹시 같은 종목에서 Long1 시그널 중복 발생시 후속타 무시
    2. bot.get_amount() 대신 bot.get_amount_hatiko2()를 씀. 트뷰와 무관하게 그냥 전체 자금 기준 8분할하는 방식으로 매매 수량을 정함.(청산당할MDD보정 포함되어 있음)
    """
    global baseLong1_list, baseLong2_list, baseLong3_list, baseLong4_list
    global baseShort1_list, baseShort2_list, baseShort3_list, baseShort4_list
    global nMaxTry

    # hatiko4 상수
    nMaxLong = 2    # 최대 1종목 몰빵투자
    nMaxShort = 1   # 최대 1종목 몰빵투자

    # 초기화 단계
    result = None
    nGoal = 0
    nComplete = 0

    # [Debug] 트뷰 시그널이 도착했다는 알람 발생
    background_tasks.add_task(log_recv_message, order_info)

    # nMaxTry 횟수만큼 자동매매 시도
    for nTry in range(nMaxTry):
        if nGoal != 0 and nComplete == nGoal:   # 이미 매매를 성공하면 더이상의 Try를 생략함.
            break

        try:
            # 엔트리 주문 중복 무시
            if (len(baseLong1_list) >= nMaxLong or order_info.base in baseLong1_list) and order_info.order_name == "Long1":
                return {"result" : "ignore"}
            if (len(baseLong2_list) >= nMaxLong or order_info.base in baseLong2_list) and order_info.order_name == "Long2":
                return {"result" : "ignore"}
            if (len(baseLong3_list) >= nMaxLong or order_info.base in baseLong3_list) and order_info.order_name == "Long3":
                return {"result" : "ignore"}
            if (len(baseLong4_list) >= nMaxLong or order_info.base in baseLong4_list) and order_info.order_name == "Long4":
                return {"result" : "ignore"}
            if (len(baseShort1_list) >= nMaxShort or order_info.base in baseShort1_list) and order_info.order_name == "Short1":
                return {"result" : "ignore"}
            if (len(baseShort2_list) >= nMaxShort or order_info.base in baseShort2_list) and order_info.order_name == "Short2":
                return {"result" : "ignore"}
            if (len(baseShort3_list) >= nMaxShort or order_info.base in baseShort3_list) and order_info.order_name == "Short3":
                return {"result" : "ignore"}
            if (len(baseShort4_list) >= nMaxShort or order_info.base in baseShort4_list) and order_info.order_name == "Short4":
                return {"result" : "ignore"}
            
            # 안 산 주문에 대한 종료 무시
            if order_info.side.startswith("close/"):
                if order_info.base not in (baseLong1_list + baseLong2_list + baseLong3_list + baseLong4_list + baseShort1_list + baseShort2_list + baseShort3_list + baseShort4_list):
                    return {"result" : "ignore"}
                if order_info.order_name in ["TakeProfitS2", "TakeProfitS3", "TakeProfitS4", "TakeProfitL2", "TakeProfitL3", "TakeProfitL4"]:
                    return {"result" : "ignore"}

            exchange_name = order_info.exchange.upper()
            exchange = get_exchange(exchange_name, order_info.kis_number)
            if exchange_name in ("BINANCE"):    # Binance Only
                bot = exchange.dict()[order_info.exchange]
                bot.order_info = order_info
                if order_info.side.startswith("entry/"):
                    if order_info.stop_price and order_info.profit_price:
                        pass
                    else:
                        ###################################
                        # Entry 매매 코드
                        ###################################
                        
                        if nTry == 0:   # 초기 세팅
                            symbol = bot.parse_symbol(order_info.base, order_info.quote)
                            side = bot.parse_side(order_info.side)
                            quote = bot.parse_quote(order_info.quote)
                            if order_info.leverage is not None:
                                bot.future.set_leverage(order_info.leverage, symbol)
                            # total amount를 max_amount로 쪼개기
                            total_amount = bot.get_amount_hatiko2(order_info.base, quote)
                            max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                            min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"] 
                            # Set nGoal
                            entry_amount_list = []
                            if (total_amount % max_amount < min_amount):
                                nGoal = total_amount // max_amount
                                for i in range(int(nGoal)):
                                    entry_amount_list.append(max_amount)
                            else:
                                nGoal = total_amount // max_amount + 1
                                for i in range(int(nGoal - 1)):
                                    entry_amount_list.append(max_amount)
                                entry_amount_list.append(total_amount % max_amount)
                            # 시장가를 지정가로 변환
                            # 슬리피지 0.8프로 짜리 지정가로 변환
                            # 트뷰 시그널 가격과 1%의 괴리가 있으면 시그널 무시
                            current_price = bot.fetch_price(order_info.base, quote)
                            if order_info.order_name in ["Long1", "Long2", "Long3", "Long4"] and current_price > order_info.price * 1.01:
                                return {"result" : "ignore"}
                            if order_info.order_name in ["Short1", "Short2", "Short3", "Short4"] and current_price < order_info.price * 0.99:
                                return {"result" : "ignore"}
                            slipage = 0.8
                            if side == "buy":
                                entry_price = current_price * (1 + slipage / 100)
                            if side == "sell":
                                entry_price = current_price * (1 - slipage / 100) 
                            
                        # 매매 주문
                        for i in range(int(nGoal-nComplete)):
                            entry_amount = entry_amount_list[nComplete]
                            result = bot.future.create_order(symbol, "limit", side, abs(entry_amount), entry_price)
                            nComplete += 1
                            # 디스코드 로그생성
                            background_tasks.add_task(log, exchange_name, result, order_info)
                        
                        # 매매가 전부 종료되면
                        # 매매종목 리스트 업데이트
                        if order_info.order_name == "Long1":
                            baseLong1_list.append(order_info.base)
                        if order_info.order_name == "Long2":
                            baseLong2_list.append(order_info.base)  
                        if order_info.order_name == "Long3":
                            baseLong3_list.append(order_info.base)
                        if order_info.order_name == "Long4":
                            baseLong4_list.append(order_info.base)
                        if order_info.order_name == "Short1":
                            baseShort1_list.append(order_info.base)
                        if order_info.order_name == "Short2":
                            baseShort2_list.append(order_info.base)
                        if order_info.order_name == "Short3":
                            baseShort3_list.append(order_info.base)
                        if order_info.order_name == "Short4":
                            baseShort4_list.append(order_info.base)


                if order_info.side.startswith("close/"):
                    # result = bot.market_close(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent)

                    #############################
                    ## Close 매매코드
                    #############################
                    if nTry == 0:   # 초기 세팅
                        symbol = bot.parse_symbol(order_info.base, order_info.quote)
                        side = bot.parse_side(order_info.side)
                        quote = bot.parse_quote(order_info.quote)
                        
                        # total amount를 max_amount로 쪼개기
                        total_amount = bot.get_amount_hatiko2(order_info.base, quote)
                        max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                        min_amount = bot.future_markets[symbol]["limits"]["amount"]["min"]
                        # Set nGoal
                        close_amount_list = []
                        if (total_amount % max_amount < min_amount):
                            nGoal = total_amount // max_amount
                            for i in range(int(nGoal)):
                                close_amount_list.append(max_amount)
                        else:
                            nGoal = total_amount // max_amount + 1
                            for i in range(int(nGoal - 1)):
                                close_amount_list.append(max_amount)
                            close_amount_list.append(total_amount % max_amount)
                        # 트뷰에 나오는 청산 가격에 그대로 청산
                        close_price = order_info.price
                    
                    # 매매 주문
                    for i in range(int(nGoal-nComplete)):
                        close_amount = close_amount_list[nComplete]
                        result = bot.future.create_order(symbol, "limit", side, close_amount, close_price, params={"reduceOnly": True})
                        nComplete += 1
                        background_tasks.add_task(log, exchange_name, result, order_info)

                    # 매매가 전부 종료된 후
                    # 매매종목 리스트 업데이트
                    if order_info.base in baseLong1_list:
                        baseLong1_list.remove(order_info.base)
                    if order_info.base in baseLong2_list:
                        baseLong2_list.remove(order_info.base)
                    if order_info.base in baseLong3_list:
                        baseLong3_list.remove(order_info.base)
                    if order_info.base in baseLong4_list:
                        baseLong4_list.remove(order_info.base)
                    if order_info.base in baseShort1_list:
                        baseShort1_list.remove(order_info.base)
                    if order_info.base in baseShort2_list:
                        baseShort2_list.remove(order_info.base)
                    if order_info.base in baseShort3_list:
                        baseShort3_list.remove(order_info.base)           
                    if order_info.base in baseShort4_list:
                        baseShort4_list.remove(order_info.base)

        except TypeError:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
        except Exception:
            background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
            log_alert_message(order_info)

        else:
            return {"result": "success"}

        finally:
            pass



@ app.post("/order")
async def order(order_info: MarketOrder, background_tasks: BackgroundTasks):
    result = None
    try:
        exchange_name = order_info.exchange.upper()
        exchange = get_exchange(exchange_name, order_info.kis_number)
        if exchange_name in ("BINANCE", "UPBIT", "BYBIT", "BITGET"):
            bot = exchange.dict()[order_info.exchange]
            bot.order_info = order_info
            if order_info.side == "buy":
                result = bot.market_buy(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent)
            elif order_info.side == "sell":
                result = bot.market_sell(order_info.base, order_info.quote, order_info.type,
                                         order_info.side, order_info.amount, order_info.price, order_info.percent)
            elif order_info.side.startswith("entry/"):
                if order_info.stop_price and order_info.profit_price:
                    result = bot.market_sltp_order(order_info.base, order_info.quote, order_info.type,
                                                   order_info.side, order_info.amount, order_info.stop_price, order_info.profit_price)
                else:
                    result = bot.market_entry(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent, order_info.leverage)
            elif order_info.side.startswith("close/"):
                result = bot.market_close(order_info.base, order_info.quote, order_info.type, order_info.side, order_info.amount, order_info.price, order_info.percent)
            background_tasks.add_task(log, exchange_name, result, order_info)
        elif exchange_name in ("KRX", "NASDAQ", "NYSE", "AMEX"):
            kis: KoreaInvestment = exchange
            result = kis.create_order(order_info.exchange, order_info.base, order_info.type.lower(), order_info.side.lower(), order_info.amount)
            background_tasks.add_task(log, exchange_name, result, order_info)

    except TypeError:
        background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
    except Exception:
        background_tasks.add_task(log_order_error_message, traceback.format_exc(), order_info)
        log_alert_message(order_info)

    else:
        return {"result": "success"}

    finally:
        pass

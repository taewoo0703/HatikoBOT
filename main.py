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
from utility import settings, log_order_message, log_alert_message, print_alert_message, logger_test, log_order_error_message, log_validation_error_message
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

@app.get("/version")
async def version():
    return "2023-01-25 version. 에러가 나도 최대 5번까지 매매 시도함"

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
                        
                        symbol = bot.parse_symbol(order_info.base, order_info.quote)
                        side = bot.parse_side(order_info.side)
                        quote = bot.parse_quote(order_info.quote)
                        if order_info.leverage is not None:
                            bot.future.set_leverage(order_info.leverage, symbol)
                        # total amount를 max_amount로 쪼개기
                        total_amount = bot.get_amount(order_info.base, quote, order_info.amount, order_info.percent)
                        max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                        # Set nGoal
                        entry_amount_list = []
                        if (total_amount % max_amount == 0):
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
                        current_price = bot.fetch_price(order_info.base, quote)
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
                    symbol = bot.parse_symbol(order_info.base, order_info.quote)
                    side = bot.parse_side(order_info.side)
                    quote = bot.parse_quote(order_info.quote)
                    
                    # total amount를 max_amount로 쪼개기
                    total_amount = bot.get_amount(order_info.base, quote, order_info.amount, order_info.percent)
                    max_amount = bot.future_markets[symbol]["limits"]["amount"]["max"] # 지정가 주문 최대 코인개수
                    # Set nGoal
                    close_amount_list = []
                    if (total_amount % max_amount == 0):
                        nGoal = total_amount // max_amount
                        for i in range(int(nGoal)):
                            close_amount_list.append(max_amount)
                    else:
                        nGoal = total_amount // max_amount + 1
                        for i in range(int(nGoal - 1)):
                            close_amount_list.append(max_amount)
                        close_amount_list.append(total_amount % max_amount)
                    # 시장가를 지정가로 변환
                    # 슬리피지 0.8프로 짜리 지정가로 변환
                    current_price = bot.fetch_price(order_info.base, quote)
                    slipage = 0.8
                    if side == "buy":
                        close_price = current_price * (1 + slipage / 100)
                    if side == "sell":
                        close_price = current_price * (1 - slipage / 100)
                    
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

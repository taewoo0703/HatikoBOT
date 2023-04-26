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
nMaxTry = 5

# 시장가 Hatiko용 리스트
baseLong1_list = []
baseLong2_list = []
baseLong3_list = []
baseLong4_list = []
baseShort1_list = []
baseShort2_list = []
baseShort3_list = []
baseShort4_list = []

# 지정가 Hatiko용 near시그널 딕셔너리
# base(종목명) : orderID_list(오더id 리스트)
nearLong1_dic = {}
nearLong2_dic = {}
nearLong3_dic = {}
nearLong4_dic = {}
nearShort1_dic = {}
nearShort2_dic = {}
nearShort3_dic = {}
nearShort4_dic = {}

# 지정가 Hatiko용 entry시그널 리스트
Long1_list = []
Long2_list = []
Long3_list = []
Long4_list = []
Short1_list = []
Short2_list = []
Short3_list = []
Short4_list = []

def matchNearDic(order_name):
    """
    order_name에 따라 해당하는 near딕셔너리를 반환
    예시) input : "NextCandle_L1" -> output : "nearLong1_dic"
    """
    global nearLong1_dic, nearLong2_dic, nearLong3_dic, nearLong4_dic, nearShort1_dic, nearShort2_dic, nearShort3_dic, nearShort4_dic

    if order_name in ["nearLong1", "Long1", "NextCandle_L1"]:
        return nearLong1_dic
    if order_name in ["nearLong2", "Long2", "NextCandle_L2"]:
        return nearLong2_dic
    if order_name in ["nearLong3", "Long3", "NextCandle_L3"]:
        return nearLong3_dic
    if order_name in ["nearLong4", "Long4", "NextCandle_L4"]:
        return nearLong4_dic
    if order_name in ["nearShort1", "Short1", "NextCandle_S1"]:
        return nearShort1_dic
    if order_name in ["nearShort2", "Short2", "NextCandle_S2"]:
        return nearShort2_dic
    if order_name in ["nearShort3", "Short3", "NextCandle_S3"]:
        return nearShort3_dic
    if order_name in ["nearShort4", "Short4", "NextCandle_S4"]:
        return nearShort4_dic

def matchEntryList(order_name):
    """
    order_name에 따라 해당하는 entry리스트를 반환
    예시) input : "NextCandle_L1" -> output : "Long1"
    """
    global Long1_list, Long2_list, Long3_list, Long4_list, Short1_list, Short2_list, Short3_list, Short4_list

    if order_name in ["nearLong1", "Long1", "NextCandle_L1"]:
        return Long1_list
    if order_name in ["nearLong2", "Long2", "NextCandle_L2"]:
        return Long2_list
    if order_name in ["nearLong3", "Long3", "NextCandle_L3"]:
        return Long3_list
    if order_name in ["nearLong4", "Long4", "NextCandle_L4"]:
        return Long4_list
    if order_name in ["nearShort1", "Short1", "NextCandle_S1"]:
        return Short1_list
    if order_name in ["nearShort2", "Short2", "NextCandle_S2"]:
        return Short2_list
    if order_name in ["nearShort3", "Short3", "NextCandle_S3"]:
        return Short3_list
    if order_name in ["nearShort4", "Short4", "NextCandle_S4"]:
        return Short4_list

@app.get("/version")
async def version():
    return "2023-04-23, Hatiko 지정가 버전 추가"

@ app.get("/hatikoInfo")
async def hatikoInfo():
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
                if order_info.order_name in ["TakeProfit_S2", "TakeProfit_S3", "TakeProfit_S4", "TakeProfit_L2", "TakeProfit_L3", "TakeProfit_L4"]:
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
                if order_info.order_name in ["TakeProfit_S2", "TakeProfit_S3", "TakeProfit_S4", "TakeProfit_L2", "TakeProfit_L3", "TakeProfit_L4"]:
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
                if order_info.order_name in ["TakeProfit_S2", "TakeProfit_S3", "TakeProfit_S4", "TakeProfit_L2", "TakeProfit_L3", "TakeProfit_L4"]:
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

@ app.post("/hatikolimit")
async def hatikolimit(order_info: MarketOrder, background_tasks: BackgroundTasks):
    """
    지정가 Hatiko 전략

    [트뷰]
    nearLong1 : Long1 가격 근처에 갔을 때 발생. Long1 가격을 전달함.
    Long1 : Long1 가격 도달 시 발생
    NextCandle_L1 : nearLong1 시그널 발생 후 청산 전까지 봉마감 할 때마다 발생. 새로운 Level_Long1 가격을 전달함.
    Close 및 Exit : 청산 조건 달성 시 발생

    [하티코봇]
    1. nearLong1 시그널 수신
    nearLong1_list 최대개수 확인 -> 미달 시, 지정가 매수주문 -> 성공 시, nearLong1_list에 추가

    2. NextCandle_L1 시그널 수신
    해당 종목이 nearLong1_list에 존재하는지 확인 -> 존재 시, Long1_list에 없으면 미체결주문 체크 -> 미체결주문 취소 & 신규 Long1 주문

    3. Long1 시그널 수신
    해당 종목이 nearLong1_list에 존재하는지 확인 -> 존재 시, Long1 리스트에 추가

    4. 청산 시그널 수신
    해당 종목이 nearLong1_list에 존재하는지 확인 -> 존재 시, 청산 주문 -> 성공 시, 존재하는 모든 리스트에서 제거
    """
    global nearLong1_dic, nearLong2_dic, nearLong3_dic, nearLong4_dic
    global nearShort1_dic, nearShort2_dic, nearShort3_dic, nearShort4_dic
    global Long1_list, Long2_list, Long3_list, Long4_list
    global Short1_list, Short2_list, Short3_list, Short4_list
    global nMaxTry

    # order_name 리스트
    nearSignal_list = ["nearLong1", "nearLong2", "nearLong3", "nearLong4",
                       "nearShort1", "nearShort2", "nearShort3", "nearShort4"]
    entrySignal_list = ["Long1", "Long2", "Long3", "Long4",
                        "Short1", "Short2", "Short3", "Short4"]
    nextSignal_list = ["NextCandle_L1", "NextCandle_L2", "NextCandle_L3", "NextCandle_L4",
                       "NextCandle_S1", "NextCandle_S2", "NextCandle_S3", "NextCandle_S4"]
    closeSignal_list = ["close Longs on open", "close Shorts on open",
                        "TakeProfit_nearL1", "TakeProfit_nearS1"]


    # 종목개수 선정
    nMaxLong = 1    # 최대 1종목 몰빵투자
    nMaxShort = 1   # 최대 1종목 몰빵투자

    # 초기화 단계
    result = None
    nGoal = 0
    nComplete = 0
    isSettingFinish = False     # 매매전 ccxt 세팅 flag 
    orderID_list = []           # 오더id 리스트
    isCancelSuccess = False        # 청산주문시 미체결주문 취소성공 여부

    # [Debug] 트뷰 시그널이 도착했다는 알람 발생
    background_tasks.add_task(log_recv_message, order_info)

    # nMaxTry 횟수만큼 자동매매 시도
    for nTry in range(nMaxTry):
        if nGoal != 0 and nComplete == nGoal:   # 이미 매매를 성공하면 더이상의 Try를 생략함.
            break

        try:
            if order_info.order_name in nearSignal_list:
                # near 시그널 처리
                # 예시) nearLong1 시그널 수신
                # nearLong1_dic 최대개수 확인 -> 미달 시, 지정가 매수주문 -> 성공 시, nearLong1_dic에 추가
                
                # 1. 종목 최대개수 확인
                near_dic = matchNearDic(order_info.order_name)
                if order_info.side == "entry/buy" and (len(near_dic) >= nMaxLong or order_info.base in near_dic):
                    return {"result" : "ignore"}
                if order_info.side == "entry/sell" and (len(near_dic) >= nMaxShort or order_info.base in near_dic):
                    return {"result" : "ignore"}

                # 2. 지정가 Entry 주문 (기존코드 재활용)
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
                            if nTry == 0 and not isSettingFinish:   # 초기 세팅
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
                                # 진입 가격은 order_info로 넘겨받음
                                entry_price = order_info.price
                                isSettingFinish = True

                            # 매매 주문
                            for i in range(int(nGoal-nComplete)):
                                entry_amount = entry_amount_list[nComplete]
                                result = bot.future.create_order(symbol, "limit", side, abs(entry_amount), entry_price)
                                orderID_list.append(result['id'])
                                nComplete += 1
                                # 디스코드 로그생성
                                background_tasks.add_task(log, exchange_name, result, order_info)

                            # 매매가 전부 종료되면
                            # near리스트 업데이트
                            near_dic[order_info.base] = orderID_list

            if order_info.order_name in entrySignal_list:
                # Long or Short 시그널 처리
                # 예시) Long1 시그널 수신
                # 해당 종목이 nearLong1_dic에 존재하는지 확인 -> 존재 시, Long1 리스트에 추가
                
                near_dic = matchNearDic(order_info.order_name)
                entry_list = matchEntryList(order_info.order_name)
                if order_info.base in near_dic:
                    entry_list.append(order_info.base)

            if order_info.order_name in nextSignal_list:
                # NextCandle 시그널 처리
                # 예시) NextCandle_L1 시그널 수신
                # 해당 종목이 nearLong1_dic에 존재하는지 확인 -> 존재 시, Long1_list에 없으면 미체결주문 체크 -> 미체결주문 취소 & 신규 Long1 주문
                
                # 1. 봉마감 후 재주문이 필요없으면 무시
                near_dic = matchNearDic(order_info.order_name)
                entry_list = matchEntryList(order_info.order_name)
                if order_info.base not in near_dic or order_info.base in entry_list: 
                    return {"result" : "ignore"}

                # 2. 미체결 주문 변경
                exchange_name = order_info.exchange.upper()
                exchange = get_exchange(exchange_name, order_info.kis_number)
                if exchange_name in ("BINANCE"):    # Binance Only
                    bot = exchange.dict()[order_info.exchange]
                    bot.order_info = order_info
                    symbol = bot.parse_symbol(order_info.base, order_info.quote)
                    side = bot.parse_side(order_info.side)
                    quote = bot.parse_quote(order_info.quote)
                    
                    # 변경할 near_dic 선정
                    near_dic = matchNearDic(order_info.order_name)

                    # 주문 변경
                    orderID_list_old = near_dic[order_info.base]
                    for orderID in orderID_list_old:
                        order = bot.future.fetch_order(orderID, symbol)
                        result = bot.future.edit_order(orderID, symbol, "limit", order['side'], order['remaining'], order_info.price)
                        orderID_list.append(result['id'])
                        background_tasks.add_task(log, exchange_name, result, order_info)
                    
                    # near_dic 오더id 업데이트
                    near_dic[order_info.base] = orderID_list

            if order_info.order_name in closeSignal_list:
                # 청산 시그널 처리
                # 예시) 청산 시그널 수신
                # 해당 종목이 nearLong1_list에 존재하는지 확인 -> 존재 시, 청산 주문 & 미체결 주문 취소 -> 성공 시, 존재하는 모든 리스트에서 제거
                
                # 1. 안 산 주문에 대한 종료 무시
                if order_info.base not in (list(nearLong1_dic) + list(nearLong2_dic) + list(nearLong3_dic) + list(nearLong4_dic) + \
                                           list(nearShort1_dic) + list(nearShort2_dic) + list(nearShort3_dic) + list(nearShort4_dic)):
                    return {"result" : "ignore"}

                # 2. 청산 주문(기존 코드 재사용) & 미체결 주문 취소
                exchange_name = order_info.exchange.upper()
                exchange = get_exchange(exchange_name, order_info.kis_number)
                if exchange_name in ("BINANCE"):    # Binance Only
                    bot = exchange.dict()[order_info.exchange]
                    bot.order_info = order_info
                    if order_info.side.startswith("close/"):
                        #############################
                        ## Close 매매코드
                        #############################
                        if nTry == 0 and not isSettingFinish:   # 초기 세팅
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
                            isSettingFinish = True

                        # (1) 미체결 주문 취소
                        if not isCancelSuccess:
                            bot.future.cancel_all_orders(symbol)
                            isCancelSuccess = True

                        # (2) 청산 주문
                        for i in range(int(nGoal-nComplete)):
                            close_amount = close_amount_list[nComplete]
                            result = bot.future.create_order(symbol, "limit", side, close_amount, close_price, params={"reduceOnly": True})
                            nComplete += 1
                            background_tasks.add_task(log, exchange_name, result, order_info)



                        # 매매가 전부 종료된 후
                        # 매매종목 리스트 업데이트
                        if order_info.base in nearLong1_dic:
                            nearLong1_dic.pop(order_info.base)
                        if order_info.base in nearLong2_dic:
                            nearLong2_dic.pop(order_info.base)
                        if order_info.base in nearLong3_dic:
                            nearLong3_dic.pop(order_info.base)
                        if order_info.base in nearLong4_dic:
                            nearLong4_dic.pop(order_info.base)
                        if order_info.base in nearShort1_dic:
                            nearShort1_dic.pop(order_info.base)
                        if order_info.base in nearShort2_dic:
                            nearShort2_dic.pop(order_info.base)
                        if order_info.base in nearShort3_dic:
                            nearShort3_dic.pop(order_info.base)
                        if order_info.base in nearShort4_dic:
                            nearShort4_dic.pop(order_info.base)

                        if order_info.base in Long1_list:
                            Long1_list.remove(order_info.base)
                        if order_info.base in Long2_list:
                            Long2_list.remove(order_info.base)
                        if order_info.base in Long3_list:
                            Long3_list.remove(order_info.base)
                        if order_info.base in Long4_list:
                            Long4_list.remove(order_info.base)
                        if order_info.base in Short1_list:
                            Short1_list.remove(order_info.base)
                        if order_info.base in Short2_list:
                            Short2_list.remove(order_info.base)
                        if order_info.base in Short3_list:
                            Short3_list.remove(order_info.base)
                        if order_info.base in Short4_list:
                            Short4_list.remove(order_info.base)

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
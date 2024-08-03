import numpy as np
import talib
from typing import List

def getOperateDirection(histPrice, stage: int):
    """
    获取当前均线方向
    """
    MAX = talib.MA(histPrice["close"], stage)
    MAX_2 = talib.MA(histPrice["close"], stage // 2)
    MAX_4 = talib.MA(histPrice["close"], stage // 4)
    maxGapPercentage: float = 0.02
    if MAX_4.iloc[-2] > MAX.iloc[-2] and MAX_2.iloc[-2] > MAX.iloc[-2]:
        return 1
    elif MAX_4.iloc[-2] < MAX.iloc[-2] and MAX_2.iloc[-2] < MAX.iloc[-2]:
        return -1
    else:
        gapPercentage = abs((MAX_4.iloc[-2] - MAX.iloc[-2]) / MAX.iloc[-2])
        if gapPercentage < maxGapPercentage:
            return 1 if MAX_2.iloc[-2] > MAX.iloc[-2] else -1
    return 0

def MACD(data, fast_period=10, slow_period=20, singal_period=5):
    fastMA = talib.MA(data, fast_period)
    slowMA = talib.MA(data, slow_period)
    macdLine: List[float] = np.array(fastMA, dtype=float) - np.array(slowMA, dtype=float)
    signalLine = talib.MA(macdLine, singal_period)
    macdList = macdLine - np.array(signalLine)
    return macdLine, signalLine, macdList

def checkMACDCross(histPrice, stage: int):
    """
    crossType为1表示金叉，为-1表示死叉，为0表示没有
    diffZeroAxis为1表示在DIFF>10时出现的，为-1表示在DIFF<-10出现的，为0表示在[-10,10]区间出现的
    """
    # DIFF, DEA, _MACD = talib.MACD(histPrice["Close"], stage // 2, stage, stage // 4)
    DIFF, DEA, _MACD = MACD(histPrice["close"], stage // 2, stage, stage // 4)
    if len(DIFF) < 2 or len(DEA) < 2:
        return (0, 0)
    latest_DIFF = DIFF[-1]
    previous_DIFF = DIFF[-2]
    latest_DEA = DEA[-1]
    previous_DEA = DEA[-2]
    crossType = 0
    diffZeroAxis = 0
    # 金叉条件
    if latest_DIFF > latest_DEA and previous_DIFF <= previous_DEA:
        crossType = 1
    # 死叉条件
    elif latest_DIFF < latest_DEA and previous_DIFF >= previous_DEA:
        crossType = -1
    else:
        crossType = 0
    if abs(latest_DIFF) <= 10:
        diffZeroAxis = 0
    else:
        if latest_DIFF < 0:
            diffZeroAxis = -1
        else:
            diffZeroAxis = 1
    return (crossType, diffZeroAxis)

def operateWarn(direct_20: int, direct_80: int, direct_320: int) -> int:
    """
    为±2表示1h和4h趋势方向一致，15min回调
    为±1表示1h和4h趋势方向一致，15min也一致或模糊，此时应该是持仓等等
    为0表示1h和4h趋势方向不一致，不操作
    """
    if direct_80 == -1 and direct_320 == -1:
        if direct_20 == 1:
            return -2
        else:
            return -1
    elif direct_80 == 1 and direct_320 == 1:
        if direct_20 == -1:
            return 2
        else:
            return 1
    else:
        return 0

def macdCrossWarn(corssType: int, diffZeroAxis: int):
    """
    为±3表示金死叉
    为2表示零轴上的金叉，为-2表示零轴下的死叉，都代表着原先趋势延续
    为±1表示零轴附近的金死叉，是弱势金死叉
    为0表示没有
    """
    if corssType == 1:
        if diffZeroAxis == -1:
            return 3
        elif diffZeroAxis == 1:
            return 2
        else:
            return 1
    elif corssType == -1:
        if diffZeroAxis == 1:
            return -3
        elif diffZeroAxis == -1:
            return -2
        else:
            return -1
    else:
        return 0

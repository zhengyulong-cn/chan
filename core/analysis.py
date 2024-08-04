import numpy as np
import pandas as pd
import talib
from typing import List

def getOperateDirection(histPrice: pd.DataFrame, *, stage: int, offset: int):
    """
    获取当前均线方向
    """
    MAX = talib.MA(histPrice["close"], stage)
    MAX_2 = talib.MA(histPrice["close"], stage // 2)
    MAX_4 = talib.MA(histPrice["close"], stage // 4)
    compareIdx = -2 - offset
    if abs(compareIdx) > len(histPrice):
        return 0
    if MAX_4.iloc[compareIdx] > MAX.iloc[compareIdx] and MAX_2.iloc[compareIdx] > MAX.iloc[compareIdx]:
        return 1
    elif MAX_4.iloc[compareIdx] < MAX.iloc[compareIdx] and MAX_2.iloc[compareIdx] < MAX.iloc[compareIdx]:
        return -1
    return 0

def getPenMaxMinPrice(histPrice: pd.DataFrame, startIdx: int, endIdx: int, direct: int, nearCheckDelta: int):
    if direct == 1:
        lowMinPrice = histPrice.iloc[startIdx: endIdx]["low"].min()
        lowMinPriceIdx = histPrice.iloc[startIdx: endIdx]["low"].idxmin()
        nesarLowMinPrice = histPrice[lowMinPriceIdx - nearCheckDelta: lowMinPriceIdx]["low"].min()
        if nesarLowMinPrice < lowMinPrice:
            lowMinPrice = nesarLowMinPrice
            lowMinPriceIdx = histPrice[lowMinPriceIdx - nearCheckDelta: lowMinPriceIdx]["low"].idxmin()
        return {
            "maxMinPrice": lowMinPrice,
            "maxMinPriceIdx": lowMinPriceIdx,
            "type": "buttom" if direct == 1 else "top",
            "datetime": histPrice.iloc[lowMinPriceIdx]["datetime"]
        }
    elif direct == -1:
        highMaxPrice = histPrice.iloc[startIdx: endIdx]["high"].max()
        highMaxPriceIdx = histPrice.iloc[startIdx: endIdx]["high"].idxmax()
        nesarHighMaxPrice = histPrice[highMaxPriceIdx - nearCheckDelta: highMaxPriceIdx]["high"].max()
        if nesarHighMaxPrice > highMaxPrice:
            highMaxPrice = nesarHighMaxPrice
            highMaxPriceIdx = histPrice[highMaxPriceIdx - nearCheckDelta: highMaxPriceIdx]["high"].idxmax()
        return {
            "maxMinPrice": highMaxPrice,
            "maxMinPriceIdx": highMaxPriceIdx,
            "type": "buttom" if direct == 1 else "top",
            "datetime": histPrice.iloc[highMaxPriceIdx]["datetime"]
        }
    else:
        raise ValueError("direct的值不可能为0，请检查输入数据")

def buildChanPens(histPrice: pd.DataFrame, *, type: str):
    """
    根据历史价格数据和类型构建画笔

    参数:

    histPrice : pd.DataFrame 包含历史价格数据的DataFrame。

    type : str 类型标识符，可以是"A0", "A1", 或 "A2"。

    返回: penPointList 由函数计算得出的笔的点位
    """
    if type not in ["A0", "A1", "A2"]:
        raise ValueError("Type must be one of 'A0', 'A1', or 'A2'")
    mapType2Col = {
        "A0": "a0Direct",
        "A1": "a1Direct",
        "A2": "a2Direct",
    }
    mapNearCheckDelta = {
        "A0": 10,
        "A1": 40,
        "A2": 160,
    }
    directColData = histPrice[mapType2Col[type]]
    penDirect = 0
    penSwitchList = []
    for i, curDirect in enumerate(directColData):
        if curDirect == 1 and penDirect != 1:
            penDirect = 1
            penSwitchList.append((i, penDirect))
        if curDirect == -1 and penDirect != -1:
            penDirect = -1
            penSwitchList.append((i, penDirect))
    penPointList = []
    for i, curPen in enumerate(penSwitchList):
        if i == 0:
            priceObj = getPenMaxMinPrice(histPrice, 0, curPen[0], curPen[1], mapNearCheckDelta[type])
            penPointList.append(priceObj)
        else:
            prePen = penSwitchList[i - 1]
            priceObj = getPenMaxMinPrice(histPrice, prePen[0], curPen[0], curPen[1], mapNearCheckDelta[type])
            penPointList.append(priceObj)
        if i == len(penSwitchList) - 1:
            priceObj = getPenMaxMinPrice(histPrice, curPen[0], len(histPrice), 1 if curPen[1] == -1 else -1, mapNearCheckDelta[type])
            penPointList.append(priceObj)
    return penPointList

def mergeCentralList(centralList):
    """
    将有重叠的中枢进行合并
    """
    # 保证按照最左侧坐标排序正确
    centralList.sort(key=lambda x: (x['idxRange'][0], x['priceRange'][0]))
    mergedList = []
    for interval in centralList:
        # 如果没有重叠就不合并
        if not mergedList:
            mergedList.append(interval)
        # 如果有重叠，返回True，没有则返回False
        xOverlapJudge = mergedList[-1]['idxRange'][1] > interval['idxRange'][0]
        yOverlapJudge = mergedList[-1]['priceRange'][1] > interval['priceRange'][0]
        if not xOverlapJudge and not yOverlapJudge:
            mergedList.append(interval)
        elif not xOverlapJudge and yOverlapJudge:
            mergedList.append(interval)
        elif xOverlapJudge and yOverlapJudge:
            # 与最后一个区间合并
            last = mergedList.pop()
            new_idx_range = [
                min(last['idxRange'][0], interval['idxRange'][0]),
                max(last['idxRange'][1], interval['idxRange'][1])
            ]
            new_price_range = [
                min(last['priceRange'][0], interval['priceRange'][0]),
                max(last['priceRange'][1], interval['priceRange'][1])
            ]
            mergedList.append({'idxRange': new_idx_range, 'priceRange': new_price_range})
        else:
            print("特殊情况：X轴重叠但Y轴不重叠")
    return mergedList

def getNextBigPenDirect(startIdx: int, endIdx: int, bigPenPointList: list):
    for i, curPenPoint in enumerate(bigPenPointList):
        if i + 1 > len(bigPenPointList) - 1:
            continue
        nextPenPoint = bigPenPointList[i + 1]
        if curPenPoint['maxMinPriceIdx'] <= startIdx and endIdx <= nextPenPoint['maxMinPriceIdx']:
            if curPenPoint["type"] == "top":
                return -1
            else:
                return 1
    return 0

def buildChanCentral(*, penPointList, bigPenPointList):
    """
    根据历史价格数据、笔的点位、级别类型构建中枢

    参数:

    histPrice : pd.DataFrame 包含历史价格数据的DataFrame。

    penPointList : list 笔的点位

    bigPenPointList : list 笔的点位

    返回:
    int
        由函数计算得出的整数值。
    """
    centralList = []
    for i, curPoint in enumerate(penPointList):
        if i < 3:
            continue
        second2LastPoint = penPointList[i - 1]
        third2LastPoint = penPointList[i - 2]
        fourth2LastPoint = penPointList[i - 3]
        curPointIdx = curPoint["maxMinPriceIdx"]
        fourth2LastPointIdx = fourth2LastPoint["maxMinPriceIdx"]

        bigDirect = getNextBigPenDirect(fourth2LastPointIdx, curPointIdx, bigPenPointList)
        if bigDirect == 1:
            if curPoint["maxMinPrice"] < fourth2LastPoint["maxMinPrice"] and second2LastPoint["maxMinPrice"] > third2LastPoint["maxMinPrice"]:
                maxminPrice = min(second2LastPoint["maxMinPrice"], fourth2LastPoint["maxMinPrice"])
                minMaxPrice = max(curPoint["maxMinPrice"], third2LastPoint["maxMinPrice"])
                centralList.append({
                    "idxRange": [fourth2LastPoint["maxMinPriceIdx"], curPoint["maxMinPriceIdx"]],
                    "priceRange": [minMaxPrice, maxminPrice],
                })
        if bigDirect == -1:
            if curPoint["maxMinPrice"] > fourth2LastPoint["maxMinPrice"] and second2LastPoint["maxMinPrice"] < third2LastPoint["maxMinPrice"]:
                maxminPrice = min(curPoint["maxMinPrice"], third2LastPoint["maxMinPrice"])
                minMaxPrice = max(second2LastPoint["maxMinPrice"], fourth2LastPoint["maxMinPrice"])
                centralList.append({
                    "idxRange": [fourth2LastPoint["maxMinPriceIdx"], curPoint["maxMinPriceIdx"]],
                    "priceRange": [minMaxPrice, maxminPrice],
                })
    return mergeCentralList(centralList)

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

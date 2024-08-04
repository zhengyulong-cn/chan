from core.config import FUTURE_INSTRUMENTS, KLineLevel
import core.analysis
import core.ui
import akshare as ak

class Future:
    symbol: str = ''
    def __init__(self, symbol, period) -> None:
        self.symbol = symbol
        self.histPrice = ak.futures_zh_minute_sina(symbol=self.symbol, period=period)
        self.a0PenPointList = []
        self.a1PenPointList = []
        self.a2PenPointList = []
        self.a0CentralList = []
        self.a1CentralList = []
        self.analysis()

    def analysis(self):
        self.analysisDirect()
        self.analysisChanPens()
        self.analysisChanCentral()

    def analysisDirect(self):
        self.histPrice["a0Direct"] = None
        self.histPrice["a1Direct"] = None
        self.histPrice["a2Direct"] = None
        for i in range(len(self.histPrice) - 1, -1, -1):
            offset = len(self.histPrice) - 1 - i
            self.histPrice.loc[i, "a0Direct"] = core.analysis.getOperateDirection(self.histPrice, stage=20, offset=offset)
            self.histPrice.loc[i, "a1Direct"] = core.analysis.getOperateDirection(self.histPrice, stage=80, offset=offset)
            self.histPrice.loc[i, "a2Direct"] = core.analysis.getOperateDirection(self.histPrice, stage=320, offset=offset)
    
    def analysisChanPens(self):
        self.a0PenPointList = core.analysis.buildChanPens(self.histPrice, type="A0")
        self.a1PenPointList = core.analysis.buildChanPens(self.histPrice, type="A1")
        self.a2PenPointList = core.analysis.buildChanPens(self.histPrice, type="A2")

    def analysisChanCentral(self):
        self.a0CentralList = core.analysis.buildChanCentral(penPointList=self.a0PenPointList, bigPenPointList=self.a1PenPointList)
        self.a1CentralList = core.analysis.buildChanCentral(penPointList=self.a1PenPointList, bigPenPointList=self.a2PenPointList)

def onTick():
    symbol = FUTURE_INSTRUMENTS[0]
    future = Future(symbol, str(KLineLevel.Level_15M.value))
    # future.histPrice.to_csv("histPrice.csv")
    chanMarkLine = {
        "a0PenPointList": future.a0PenPointList,
        "a1PenPointList": future.a1PenPointList,
        "a2PenPointList": future.a2PenPointList,
    }
    chanCentral = {
        "a0CentralList": future.a0CentralList,
        "a1CentralList": future.a1CentralList,
    }
    kLineRender = core.ui.KLineRender(
        symbol,
        future.histPrice,
        str(KLineLevel.Level_15M.value),
        chanMarkLine,
        chanCentral,
    )
    kLineRender.draw()

if __name__ == "__main__":
    onTick()
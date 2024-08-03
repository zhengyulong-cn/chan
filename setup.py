from core.config import FutureInstruments, KLineLevel
import pandas as pd
import akshare as ak

class Future:
    symbol: str = ''
    def __init__(self, symbol) -> None:
        self.symbol = symbol
        histPrice15 = ak.futures_zh_minute_sina(symbol=self.symbol, period=str(KLineLevel.Level_15M.value))
        print(histPrice15)


def onTick():
    print(FutureInstruments)
    Future(FutureInstruments[0])

if __name__ == "__main__":
    onTick()
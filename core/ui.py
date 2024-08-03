from pyecharts.charts import Kline
from pyecharts import options as opts
import pandas as pd

# 模拟股票数据
data = [
    [2320.26, 2302.6, 2287.3, 2362.94],
    [2300, 2291.3, 2288.26, 2308.38],
    [2295.35, 2346.5, 2295.35, 2346.92],
    [2347.22, 2358.98, 2337.35, 2363.8],
]

class KLineRender:
    kline = Kline(init_opts=opts.InitOpts(
        width="98vw",
        height="95vh",
        renderer="svg"
    ))
    symbol = ''
    period = ''
    histPrice: pd.DataFrame = None
    chanMarkLine = {}
    def __init__(self, symbol, histPrice, period, chanMarkLine) -> None:
        self.histPrice = histPrice
        self.symbol = symbol
        self.period = period
        self.chanMarkLine = chanMarkLine
    
    def parseChanMarkLineData(self):
        data = []
        a0PenPointList = self.chanMarkLine["a0PenPointList"]
        a1PenPointList = self.chanMarkLine["a1PenPointList"]
        a2PenPointList = self.chanMarkLine["a2PenPointList"]
        for i, curPoint in enumerate(a0PenPointList):
            if i + 1 >= len(a0PenPointList):
                continue
            nextPoint = a0PenPointList[i + 1]
            data.append([
                opts.MarkLineItem(symbol="none", name="", x=curPoint["maxMinPriceIdx"], y=curPoint["maxMinPrice"], linestyle_opts=opts.LineStyleOpts(color="#000000")),
                opts.MarkLineItem(symbol="none", name="", x=nextPoint["maxMinPriceIdx"], y=nextPoint["maxMinPrice"], linestyle_opts=opts.LineStyleOpts(color="#000000")),
            ])
        for i, curPoint in enumerate(a1PenPointList):
            if i + 1 >= len(a1PenPointList):
                continue
            nextPoint = a1PenPointList[i + 1]
            data.append([
                opts.MarkLineItem(symbol="none", name="", x=curPoint["maxMinPriceIdx"], y=curPoint["maxMinPrice"], linestyle_opts=opts.LineStyleOpts(color="#1677ff")),
                opts.MarkLineItem(symbol="none", name="", x=nextPoint["maxMinPriceIdx"], y=nextPoint["maxMinPrice"], linestyle_opts=opts.LineStyleOpts(color="#1677ff")),
            ])
        for i, curPoint in enumerate(a2PenPointList):
            if i + 1 >= len(a2PenPointList):
                continue
            nextPoint = a2PenPointList[i + 1]
            data.append([
                opts.MarkLineItem(symbol="none", name="", x=curPoint["maxMinPriceIdx"], y=curPoint["maxMinPrice"], linestyle_opts=opts.LineStyleOpts(color="#ff19bf")),
                opts.MarkLineItem(symbol="none", name="", x=nextPoint["maxMinPriceIdx"], y=nextPoint["maxMinPrice"], linestyle_opts=opts.LineStyleOpts(color="#ff19bf")),
            ])
        return data



    def draw(self):
        datetimeList = self.histPrice["datetime"]
        data = self.histPrice.loc[:, ["open", "close", "low", "high"]].values.tolist()
        self.kline.add_xaxis(xaxis_data=list(datetimeList))
        self.kline.add_yaxis(series_name="15min K线", y_axis=data, itemstyle_opts=opts.ItemStyleOpts(color="#ec0000"))
        markLineData = self.parseChanMarkLineData()
        self.kline.set_series_opts(
            markline_opts=opts.MarkLineOpts(
                data=markLineData
            ),
        )
        self.kline.set_global_opts(
            legend_opts=opts.LegendOpts(is_show=True, pos_bottom=10, pos_left="center"),
            datazoom_opts=[
                opts.DataZoomOpts(
                    is_show=False,
                    type_="inside",
                    xaxis_index=[0,1],  # 这里需要修改可缩放的x轴坐标编号
                    range_start=98,
                    range_end=100,
                ),
                opts.DataZoomOpts(
                    is_show=True,
                    xaxis_index=[0,1],  # 这里需要修改可缩放的x轴坐标编号
                    type_="slider",
                    pos_top="85%",
                    range_start=98,
                    range_end=100,
                ),
            ],
            yaxis_opts=opts.AxisOpts(
                is_scale=True,
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(245, 245, 245, 0.8)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000"),
            ),
            visualmap_opts=opts.VisualMapOpts(
                is_show=False,
                dimension=2,
                series_index=5,
                is_piecewise=True,
                pieces=[
                    {"value": 1, "color": "#00da3c"},
                    {"value": -1, "color": "#ec0000"},
                ],
            ),
            axispointer_opts=opts.AxisPointerOpts(
                is_show=True,
                link=[{"xAxisIndex": "all"}],
                label=opts.LabelOpts(background_color="#777"),
            ),
            brush_opts=opts.BrushOpts(
                x_axis_index="all",
                brush_link="all",
                out_of_brush={"colorAlpha": 0.1},
                brush_type="lineX",
            ),
        )
        self.kline.render("kline_chart.html")

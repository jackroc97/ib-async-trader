import yaml
import pandas as pd

from enum import Enum

from lightweight_charts import Chart


class ChartOptions(Enum):
    NO_CHART = 0
    LIVE_CHART = 1
    POST_CHART = 2
    

class ChartUtils:
    
    @classmethod
    def create_chart(cls, chart_defn_file: str) -> Chart:
        
        stream = open(chart_defn_file, 'r')
        yml_dict: dict = yaml.load(stream, yaml.Loader)

        chart_objs = {}
        main_chart_candles = yml_dict["main_chart"]["candles"]
                
        chart = None
        for key, val in yml_dict.items():
            if key == "main_chart":
                
                # Define main chart 
                chart = Chart(inner_width=val["inner_width"], 
                                   inner_height=val["inner_height"])
                
                # Define trend lines on main chart
                lines: dict = val["lines"]
                for name, color in lines.items():
                    chart_objs[name] = chart \
                        .create_line(name, color=color, price_line=False, 
                                     price_label=False)
            # Define sub-charts
            else:
                chart_objs[key] = chart.create_subchart(
                    position=val["position"], width=val["width"], 
                    height=val["height"], sync=val["sync"])
                
                # Lines on each sub-chart
                lines: dict = val["lines"].items()
                for name, color in lines:
                    chart_objs[name] = chart_objs[key] \
                        .create_line(name, color=color, price_line=False, 
                                     price_label=False)
              
        chart._chart_objs = chart_objs
        chart._main_chart_candles = main_chart_candles
        return chart
    
    
    @classmethod
    def set_chart_data(cls, chart: Chart, data: pd.DataFrame) -> None:
        ohlcv = pd.DataFrame()
        ohlcv["time"] = data.index.to_frame()
        ohlcv["open"] = data[chart._main_chart_candles["open"]]
        ohlcv["high"] = data[chart._main_chart_candles["high"]]
        ohlcv["low"] = data[chart._main_chart_candles["low"]]
        ohlcv["close"] = data[chart._main_chart_candles["close"]]
        ohlcv["volume"] = data[chart._main_chart_candles["volume"]]
        chart.set(ohlcv)
        
        for key, val in chart._chart_objs.items():
            if val and key in data.keys():
                val.set(data)
            
    
    @classmethod
    def update_chart(cls, chart: Chart, data: pd.Series) -> None:
        ohlcv = pd.Series()
        ohlcv.name = data.name
        ohlcv["open"] = data[chart._main_chart_candles["open"]]
        ohlcv["high"] = data[chart._main_chart_candles["high"]]
        ohlcv["low"] = data[chart._main_chart_candles["low"]]
        ohlcv["close"] = data[chart._main_chart_candles["close"]]
        ohlcv["volume"] = data[chart._main_chart_candles["volume"]]
        chart._chart.update(ohlcv)    
        
        for key, val in chart._chart_objs.items():
            if val and key in data.keys():
                val.update(data)

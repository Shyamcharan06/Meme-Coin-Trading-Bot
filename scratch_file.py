import queue
import pandas as pd

class trade_data:
    def __init__(self):
        self.in_trade = False
        self.entry_price = None

        #elf.lowest_volume = None
        self.lowest_price = None
        self.short_volume_queue = queue.Queue()
        self.long_volume_queue = queue.Queue()

        self.price_queue = queue.Queue()

        self.short_size = None
        self.long_size = None

        self.symbol = None
        self.candles = None
        self.position = self.long_size

    def next(self):
        self.position += 1
        volume = float(self.candles[self.position]["v"])
        low_price = float(self.candles[self.position]["l"])

        self.lowest_volume = min(self.lowest_volume, volume)
        self.lowest_price = min(self.lowest_price, low_price)
        self.lowest_volume = volume if self.lowest_volume is None else min(self.lowest_volume, volume)
        self.lowest_price = low_price if self.lowest_price is None else min(self.lowest_price, low_price)

        self.short_volume_queue.put(volume)
        self.short_volume_queue.get()
        self.long_volume_queue.put(volume)
        self.long_volume_queue.get()


    def trading_algo()
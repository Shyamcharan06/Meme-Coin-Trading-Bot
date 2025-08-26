import queue
class TradeEngine:
    def __init__(self, candles, hyperparams):
        self.df = candles
        self.hp = hyperparams # dict of all hyperparameters
        self.in_trade = False
        self.entry_price = None
        self.lowest_price = None
        self.PV = 0
        self.trades = []
        self.position = self.hp["long_size"]

        self.volume_short = queue.Queue(maxsize=self.hp["short_size"])
        self.volume_long = queue.Queue(maxsize=self.hp["long_size"])
        self.price_sma = queue.Queue(maxsize=self.hp["sma_candles"])

    def next(self):
        self.position += 1
        row = self.df.iloc[self.position]

        curr_price = row["c"]
        curr_volume = row["v"]
        candle_low = row["l"]  # <- wick low of the candle

        # Update lowest price using candle wick
        if self.in_trade:
            if self.lowest_price is None:
                self.lowest_price = candle_low
            else:
                self.lowest_price = min(self.lowest_price, candle_low)

        # Update volume queues
        if self.volume_short.full():
            self.volume_short.get()
        self.volume_short.put(curr_volume)

        if self.volume_long.full():
            self.volume_long.get()
        self.volume_long.put(curr_volume)

        # Update SMA price queue
        if self.price_sma.full():
            self.price_sma.get()
        self.price_sma.put(curr_price)


        

    def check_entry(self):
        row = self.df.iloc[self.position]
        
        open_price = row["o"]
        close_price = row["c"]

        # Only enter on red candles
        if open_price < close_price:
            return False

        # Compute short-term and long-term volume sums
        short_vol_list = list(self.volume_short.queue)
        long_vol_list = list(self.volume_long.queue)

        if len(short_vol_list) < self.hp["short_size"] or len(long_vol_list) < self.hp["long_size"]:
            return False  # not enough data yet

        short_volume = sum(short_vol_list)
        long_volume = sum(long_vol_list)

        if (short_volume * (self.hp["long_size"] / self.hp["short_size"])) < long_volume * self.hp["volume_enter_scaler"]:
            return True

        return False

    def enter_trade(self):
        row = self.df.iloc[self.position]

        self.in_trade = True
        self.entry_price = row["c"]
        self.lowest_price = row["c"]
        #self.PV += self.hp["buy_amount"]

        self.trades.append({
            "entry_time": row["T"],
            "entry_price": self.entry_price,
            "entry_index": self.position
        })

    def check_exit(self, curr_price):
        row = self.df.iloc[self.position]

        # --- 1. Trailing stop-loss condition ---
        if curr_price > self.lowest_price * self.hp["trailing_stop_loss"]:
            return "trailing"

        # --- 2. Volume-based exit ---
        short_vol_list = list(self.volume_short.queue)
        long_vol_list = list(self.volume_long.queue)

        if len(short_vol_list) < self.hp["short_size"] or len(long_vol_list) < self.hp["long_size"]:
            return False  # Not enough volume data yet

        short_volume = sum(short_vol_list)
        long_volume = sum(long_vol_list)

        volume_ratio = short_volume * (self.hp["long_size"] / self.hp["short_size"])
        volume_threshold = long_volume * self.hp["volume_exit_scaler"]

        # Calculate SMA from the price queue
        price_list = list(self.price_sma.queue)
        if len(price_list) < self.hp["sma_candles"]:
            return False

        sma_price = sum(price_list) / len(price_list)

        if volume_ratio > volume_threshold and curr_price > sma_price:
            return "volume_sma"

        return False

    def exit_trade(self, exit_reason=None):
        row = self.df.iloc[self.position]
        exit_price = row["c"]

        raw_pnl = ((self.entry_price - exit_price) / self.entry_price) * self.hp["buy_amount"]

        entry_fee = self.hp["buy_amount"] * self.hp.get("fee_rate")
        exit_fee = (self.hp["buy_amount"] + raw_pnl) * self.hp.get("fee_rate")

        net_pnl = raw_pnl - entry_fee - exit_fee
        self.PV += net_pnl

        self.trades[-1].update({
            "exit_time": row["T"],
            "exit_price": exit_price,
            "exit_index": self.position,
            "entry_fee": entry_fee,
            "exit_fee": exit_fee,
            "net_pnl": net_pnl,
            "exit_reason": exit_reason,
            "candles_in_trade": self.position - self.trades[-1]["entry_index"]
        })

        self.in_trade = False
        self.entry_price = None
        self.lowest_price = None

    def simulate(self):
    # Start from long_size index so we have enough history
        self.position = self.hp["long_size"]

        while self.position < len(self.df) - 1:
            self.next()

            curr_price = self.df.iloc[self.position]["c"]

            if not self.in_trade:
                if self.check_entry():
                    self.enter_trade()
            else:
                exit_signal = self.check_exit(curr_price)
                if exit_signal:
                    self.exit_trade(exit_reason=exit_signal)


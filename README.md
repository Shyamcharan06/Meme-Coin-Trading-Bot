# 📈 Hyperliquid Monte Carlo Trading Simulator

A backtesting engine for evaluating a short trading strategy on Hyperliquid using historical candlestick data. The project uses a Monte Carlo search across a wide range of hyperparameters to find the optimal configuration for maximizing portfolio returns.

---

## 🚀 Features

- ✅ Connects to the [Hyperliquid API](https://hyperliquid.xyz/) to fetch historical candle data
- ✅ Custom trading strategy with volume-based entry & exit conditions
- ✅ Trailing stop-loss for exits
- ✅ Tracks trades, portfolio value (PV), and trade reasons
- ✅ Monte Carlo simulation across 2M+ hyperparameter combinations
- ✅ Saves detailed trade logs and config performance

---

## 📊 Strategy Logic

1. **Entry Condition**
   - Only enter short trades if `open > close`
   - Volume ratio:
     \[
     \text{short\_vol} \times \left(\frac{\text{long\_size}}{\text{short\_size}}\right) < \text{long\_vol} \times \text{volume\_enter\_scaler}
     \]

2. **Exit Conditions**
   - **Trailing Stop**: Exit if `current_price > lowest_price × trailing_stop_loss`
   - **Volume + SMA Exit**:
     \[
     \text{short\_vol} \times \left(\frac{\text{long\_size}}{\text{short\_size}}\right) > \text{long\_vol} \times \text{volume\_exit\_scaler}
     \]
     and `current_price > SMA(price, N)`

3. **P&L Calculation**
   - Since the strategy is short:  
     \[
     \text{PnL} = \frac{\text{entry} - \text{exit}}{\text{entry}} \times \text{buy\_amount}
     \]

---

## ⚙️ Hyperparameters

| Parameter              | Description                          |
|------------------------|--------------------------------------|
| `short_size`           | Size of short volume window          |
| `long_size`            | Size of long volume window           |
| `volume_enter_scaler`  | Entry threshold scaler               |
| `volume_exit_scaler`   | Exit threshold scaler                |
| `trailing_stop_loss`   | Trailing SL multiplier               |
| `sma_candles`          | SMA window for price filter          |
| `buy_amount`           | Capital per trade                    |

---

## 🧪 Monte Carlo Simulation

Run all combinations of hyperparameters:

```bash
python monte_carlo_runner.py
```

- Results are saved to `monte_carlo_results.csv`
- Summary is printed to console
- Easily extendable with parallelism, early stopping, or serialization

---

## 📁 File Structure

```
.
├── main.py                  # Runs one simulation
├── monte_carlo_runner.py   # Sweeps all configs
├── trade_data.py           # Trading strategy logic
├── load_candles.py         # Converts Hyperliquid JSON to DataFrame
├── monte_carlo_results.csv # Simulation output (generated)
└── README.md
```

---

## 📦 Requirements

```bash
pip install pandas numpy
pip install hyperliquid-python-sdk
```

---

## 🔮 Future Improvements

- Parallel execution with `concurrent.futures` or Ray
- Visualizations (PnL vs configs, trade markers on price)
- Advanced strategy modules (longs, leverage, commission modeling)

---



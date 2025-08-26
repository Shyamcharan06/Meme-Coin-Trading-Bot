import itertools
import time
import numpy as np
from trade_data import TradeEngine
from load_candles import candles_to_df
from hyperliquid.info import Info
from hyperliquid.utils import constants
from datetime import datetime, timezone
import pandas as pd
import concurrent.futures
import threading

# Function to run simulation for a specific parameter set
def run_simulation(params, coin_data, coins):
    short_size, long_size, v_enter, v_exit, trailing_sl, sma = params
    
    hp = {
        "short_size": short_size,
        "long_size": long_size,
        "volume_enter_scaler": v_enter,
        "volume_exit_scaler": v_exit,
        "trailing_stop_loss": trailing_sl,
        "sma_candles": sma,
        "buy_amount": 1000,
        "fee_rate": .0004  # .04% fee
    }
    
    # Create a unique key for this parameter set
    param_key = (short_size, long_size, v_enter, v_exit, trailing_sl, sma)
    
    # Test this parameter set on all coins
    total_pv = 0
    total_trades = 0
    coin_results = {}
    all_trades_for_params = []
    
    for coin in coins:
        engine = TradeEngine(coin_data[coin].copy(), hp)
        engine.simulate()
        
        coin_pv = engine.PV
        coin_trades = len(engine.trades)
        
        total_pv += coin_pv
        total_trades += coin_trades
        
        coin_results[coin] = {
            "PV": coin_pv,
            "trades": coin_trades
        }
        
        # Store trades for this parameter set
        for trade in engine.trades:
            # Add coin info to each trade
            trade_with_meta = trade.copy()  # Make a copy to avoid modifying original
            trade_with_meta['coin'] = coin
            all_trades_for_params.append(trade_with_meta)
    
    # Store results with combined performance
    result = {
        "short_size": short_size,
        "long_size": long_size,
        "v_enter": v_enter,
        "v_exit": v_exit,
        "trailing_sl": trailing_sl,
        "sma": sma,
        "total_PV": total_pv,
        "total_trades": total_trades,
        **{f"{coin}_PV": coin_results[coin]["PV"] for coin in coins},
        **{f"{coin}_trades": coin_results[coin]["trades"] for coin in coins},
        "param_key": param_key
    }
    
    return result, all_trades_for_params

# === 1. Setup ===
info = Info(constants.MAINNET_API_URL, skip_ws=True)
end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
start_time = end_time - (60 * 60 * 1000 * 1265)

# List of coins to analyze
coins = ["VINE", "TRUMP", "kPEPE"]

# Load data for all coins upfront
coin_data = {}
for coin in coins:
    print(f"Loading data for {coin}...")
    candles = info.candles_snapshot(name=coin, interval="15m", startTime=start_time, endTime=end_time)
    coin_data[coin] = candles_to_df(candles)

# === 2. Define Parameter Grid ===
short_sizes = list(range(7, 9, 2))
long_sizes = list(range(34, 42, 4))
volume_enter_scalers = [round(x, 2) for x in np.arange(0.6, 0.8, 0.1)]
volume_exit_scalers = [round(x, 2) for x in np.arange(1.1, 1.2, 0.1)]
trailing_stop_losses = [1.05, 1.1]
sma_candles = list(range(3, 7))

param_space = list(itertools.product(
    short_sizes,
    long_sizes,
    volume_enter_scalers,
    volume_exit_scalers,
    trailing_stop_losses,
    sma_candles
))

# === 3. Multithreaded Simulation Loop ===
results = []
param_trades = {}
total_start_time = time.time()

# Progress tracking variables
completed_count = 0
lock = threading.Lock()  # For thread-safe progress updates

print(f"Total parameter combinations: {len(param_space)}")
print(f"Running with 4 worker threads")

# Use ThreadPoolExecutor to run simulations in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    # Submit all parameter combinations for execution
    future_to_params = {
        executor.submit(run_simulation, params, coin_data, coins): params 
        for params in param_space
    }
    
    # Process results as they complete
    for future in concurrent.futures.as_completed(future_to_params):
        result, trades = future.result()
        param_key = result["param_key"]
        
        with lock:
            # Store results and trades
            results.append(result)
            param_trades[param_key] = trades
            
            # Update progress counter
            completed_count += 1
            
            # Display progress
            elapsed = time.time() - total_start_time
            remaining = (elapsed / completed_count) * (len(param_space) - completed_count) if completed_count > 0 else 0
            print(f"{completed_count}/{len(param_space)} parameter sets tested | Elapsed: {elapsed:.2f}s | Est. remaining: {remaining:.2f}s")

# === 4. Save Results ===
df_results = pd.DataFrame(results)
df_results.to_csv("monte_carlo_results_combined.csv", index=False)

# === 5. Analyze Results ===
# Sort by highest combined Portfolio Value
df_sorted = df_results.sort_values(by="total_PV", ascending=False)

# Get the best config
best = df_sorted.iloc[0]
best_param_key = (
    best['short_size'], 
    best['long_size'], 
    best['v_enter'], 
    best['v_exit'], 
    best['trailing_sl'], 
    best['sma']
)

print("\n🎯 Best Combined Configuration:")
print(f"Short Size           : {best['short_size']}")
print(f"Long Size            : {best['long_size']}")
print(f"Volume Enter Scaler  : {best['v_enter']}")
print(f"Volume Exit Scaler   : {best['v_exit']}")
print(f"Trailing Stop Loss   : {best['trailing_sl']}")
print(f"SMA Candles          : {best['sma']}")
print(f"Total Portfolio Value: {best['total_PV']:.2f}")
print(f"Total Trades         : {best['total_trades']}")

print("\nBreakdown by coin:")
for coin in coins:
    print(f"{coin} PV: {best[f'{coin}_PV']:.2f} | Trades: {best[f'{coin}_trades']}")

print("\n📊 Top 5 Combined Configs:")
print(df_sorted[['short_size', 'long_size', 'v_enter', 'v_exit', 
                'trailing_sl', 'sma', 'total_PV', 'total_trades'] + 
                [f"{coin}_PV" for coin in coins]].head(5))

# === 6. Print Top 3 Most Profitable and Unprofitable Trades for Best Parameter Set ===
# Get trades for the best parameter set
best_trades = param_trades[best_param_key]

# Convert to DataFrame
best_trades_df = pd.DataFrame(best_trades)

# Sort by net_pnl to find most profitable and unprofitable trades
most_profitable = best_trades_df.sort_values(by='net_pnl', ascending=False).head(3)
most_unprofitable = best_trades_df.sort_values(by='net_pnl', ascending=True).head(3)

# Print most profitable trades
print("\n💰 Top 3 Most Profitable Trades (Best Parameter Set):")
for i, (_, trade) in enumerate(most_profitable.iterrows()):
    print(f"{i+1}. Coin: {trade['coin']}")
    print(f"   Entry Time: {trade['entry_time']} at price {trade['entry_price']}")
    print(f"   Exit Time: {trade['exit_time']} at price {trade['exit_price']}")
    print(f"   Net PnL: {trade['net_pnl']:.2f}")
    print(f"   Exit Reason: {trade['exit_reason']}")
    print()

# Print most unprofitable trades
print("\n❌ Top 3 Most Unprofitable Trades (Best Parameter Set):")
for i, (_, trade) in enumerate(most_unprofitable.iterrows()):
    print(f"{i+1}. Coin: {trade['coin']}")
    print(f"   Entry Time: {trade['entry_time']} at price {trade['entry_price']}")
    print(f"   Exit Time: {trade['exit_time']} at price {trade['exit_price']}")
    print(f"   Net PnL: {trade['net_pnl']:.2f}")
    print(f"   Exit Reason: {trade['exit_reason']}")
    print()

total_elapsed = time.time() - total_start_time
print(f"\n✅ Completed {len(param_space)} parameter tests across {len(coins)} coins in {total_elapsed:.2f} seconds")
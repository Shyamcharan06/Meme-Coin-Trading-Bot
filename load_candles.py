import pandas as pd
import numpy as np

def candles_to_df(candle_json: list) -> pd.DataFrame:
    """
    Converts raw Hyperliquid candle data to a DataFrame with all original fields preserved,
    numeric types parsed, and return metrics added.
    """
    df = pd.DataFrame(candle_json)

    # Convert timestamp fields to datetime
    df["t"] = pd.to_datetime(df["t"], unit="ms")
    df["T"] = pd.to_datetime(df["T"], unit="ms")

    # Convert string fields to float
    float_cols = ["o", "c", "h", "l", "v"]
    df[float_cols] = df[float_cols].astype(float)

    # Sort by start timestamp
    df = df.sort_values("t").reset_index(drop=True)

    # Add return metrics
    df["pct_return"] = df["c"].pct_change()
    df["log_return"] = (df["c"] / df["c"].shift(1)).apply(
        lambda x: pd.NA if x <= 0 else np.log(x)
    )

    return df

from hyperliquid.info import Info

# Initialize the Info class
info = Info()

# Fetch metadata
metadata = info.meta()

# Search for Vinecoin in perpetuals
for index, asset in enumerate(metadata["universe"]):
    if asset["name"].lower() == "vinecoin":
        print(f"Vinecoin found in perpetuals with index: {index}")
        break
else:
    print("Vinecoin not found in perpetuals.")

# Search for Vinecoin in spot markets
for index, asset in enumerate(metadata["spotMeta"]["universe"]):
    if asset["name"].lower() == "vinecoin":
        print(f"Vinecoin found in spot markets with index: {index}")
        break
else:
    print("Vinecoin not found in spot markets.")

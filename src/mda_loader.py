from pathlib import Path

def load_mda_files(ticker):
    ticker = ticker.upper()
    folder = Path("data") / "raw" / ticker

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    files = list(folder.glob("*.txt"))

    if not files:
        raise ValueError(f"No .txt files found in: {folder}")

    mda_records = []

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        year = file.stem.split("_")[1]

        mda_records.append({
            "ticker": ticker,
            "year": int(year),
            "file_path": str(file),
            "text": text
        })

    return mda_records
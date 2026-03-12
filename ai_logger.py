import pandas as pd
import os
from datetime import datetime

FILE_NAME = "game_logs.csv"

def log_game(game, player, metric, value, result):
    new_row = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Game": game,
        "Player": player,
        "Metric": metric,
        "Value": float(value),
        "Result": result
    }

    df_new = pd.DataFrame([new_row])

    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(FILE_NAME, index=False)


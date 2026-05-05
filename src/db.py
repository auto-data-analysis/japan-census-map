"""
CSVからSQLiteデータベースを初期化するモジュール。
アプリ起動時にDBファイルが存在しない場合のみ実行される。
"""

import sqlite3
from pathlib import Path
import pandas as pd

# パス定義
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "raw" / "census_labor.csv"
DB_PATH = DATA_DIR / "census.db"


def init_db() -> None:
    """DBが存在しない場合のみCSVを読み込んでSQLiteに変換する。"""
    if DB_PATH.exists():
        return

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSVファイルが見つかりません: {CSV_PATH}\n"
            "data/raw/census_labor.csv を配置してください。"
        )

    df = pd.read_csv(CSV_PATH, dtype=str)

    # 不要行の除外
    # 1. 不詳補完値（推計値のため除外）
    df = df[~df["時間軸（調査年）"].str.contains("不詳補完値", na=False)]
    # 2. 労働力率（構成比は自計算するため除外）
    df = df[df["表章項目"] != "労働力率"]
    # 3. 労働力人口（就業者＋完全失業者の合計であり冗長なため除外）
    df = df[df["労働力状態３区分_時系列"] != "労働力人口"]

    # カラムの整理・型変換
    df = df.rename(columns={
        "労働力状態３区分_時系列": "labor_status",
        "男女_時系列": "gender",
        "地域_時系列": "pref",
        "時間軸（調査年）": "year_str",
    })

    # 年を整数に変換（例："2020年" → 2020）
    df["year"] = df["year_str"].str.replace("年", "").astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # 必要カラムのみ保持
    df = df[["labor_status", "gender", "pref", "year", "value"]].copy()

    # SQLiteに書き込み
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("census", conn, if_exists="replace", index=False)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_census ON census (labor_status, gender, year)"
        )


def get_db_path() -> Path:
    return DB_PATH

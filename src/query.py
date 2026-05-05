"""
SQLiteからデータを取得するクエリモジュール。
UIの選択肢取得と集計結果取得を分けて定義する。
"""

import sqlite3
import pandas as pd
from src.db import get_db_path


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(get_db_path())


# ── UIの選択肢を返す関数 ──────────────────────────────────────


def get_years() -> list[int]:
    """選択肢用：年の一覧を降順で返す。"""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT year FROM census ORDER BY year DESC"
        ).fetchall()
    return [r[0] for r in rows]


def get_labor_status_list() -> list[str]:
    """選択肢用：就業者・完全失業者・非労働力人口の3種を返す。"""
    # 総数は分母として使うためUIには表示しない
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT labor_status FROM census
            WHERE labor_status != '総数'
            ORDER BY labor_status
            """
        ).fetchall()
    # 表示順を固定
    order = ["就業者", "完全失業者", "非労働力人口"]
    available = {r[0] for r in rows}
    result = [s for s in order if s in available]
    return result


# ── 集計結果を返す関数 ────────────────────────────────────────


def fetch_choropleth(
    year: int,
    labor_status: str,
    gender: str,
) -> pd.DataFrame:
    """
    コロプレスマップ用データを返す。

    構成比(%) = 選択した労働力状態の人数 ÷ 15歳以上人口（総数）× 100

    Returns
    -------
    DataFrame with columns: pref, value, total, ratio
        pref  : 都道府県名
        value : 人数（実数）
        total : 15歳以上人口（分母）
        ratio : 構成比（%）
    """
    sql = """
        SELECT
            t.pref,
            t.value,
            d.value AS total,
            CAST(t.value AS REAL) / d.value * 100 AS ratio
        FROM census AS t
        JOIN census AS d
            ON  t.pref         = d.pref
            AND t.year         = d.year
            AND t.gender       = d.gender
            AND d.labor_status = '総数'
        WHERE
            t.labor_status = :labor_status
            AND t.gender   = :gender
            AND t.year     = :year
        ORDER BY t.pref
    """
    with _connect() as conn:
        df = pd.read_sql_query(
            sql,
            conn,
            params={
                "labor_status": labor_status,
                "gender": gender,
                "year": year,
            },
        )
    return df


def fetch_drillthrough(pref: str, year: int) -> pd.DataFrame:
    """
    ドリルスルー用：選択した都道府県・年の全労働力状態×男女別構成比を返す。

    Returns
    -------
    DataFrame（行=労働力状態、列=総数・男・女）
    """
    sql = """
        SELECT
            t.labor_status,
            t.gender,
            CAST(t.value AS REAL) / d.value * 100 AS ratio
        FROM census AS t
        JOIN census AS d
            ON  t.pref         = d.pref
            AND t.year         = d.year
            AND t.gender       = d.gender
            AND d.labor_status = '総数'
        WHERE
            t.pref         = :pref
            AND t.year     = :year
            AND t.labor_status != '総数'
        ORDER BY t.labor_status, t.gender
    """
    with _connect() as conn:
        df = pd.read_sql_query(
            sql,
            conn,
            params={"pref": pref, "year": year},
        )

    # ピボット：行=労働力状態、列=性別
    pivot = df.pivot_table(
        index="labor_status",
        columns="gender",
        values="ratio",
        aggfunc="first",
    ).reset_index()

    # 列順を固定
    col_order = ["labor_status"] + [
        c for c in ["総数", "男", "女"] if c in pivot.columns
    ]
    pivot = pivot[col_order]
    pivot.columns.name = None

    # 労働力状態の表示順を固定
    order = ["就業者", "完全失業者", "非労働力人口"]
    pivot["_order"] = pivot["labor_status"].map({s: i for i, s in enumerate(order)})
    pivot = pivot.sort_values("_order").drop(columns="_order")
    pivot = pivot.rename(columns={"labor_status": "労働力状態"})

    return pivot

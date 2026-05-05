"""
国勢調査 労働力状態 都道府県別コロプレスマップ
"""

import streamlit as st
import plotly.express as px

from src.db import init_db
from src.query import (
    get_years,
    get_labor_status_list,
    fetch_choropleth,
    fetch_drillthrough,
)

# ── 初期化 ────────────────────────────────────────────────────
init_db()

# ── ページ設定 ────────────────────────────────────────────────
st.set_page_config(
    page_title="労働力状態 都道府県マップ",
    page_icon="🗾",
    layout="wide",
)

# ── タイトル ──────────────────────────────────────────────────
st.title("🗾 労働力状態 都道府県マップ")

# ── サイドバー：フィルター ────────────────────────────────────
with st.sidebar:
    st.header("フィルター")

    # 労働力状態（3択ラジオボタン）
    labor_status = st.radio(
        "労働力状態",
        options=get_labor_status_list(),
    )

    # 性別（3択ラジオボタン）
    gender = st.radio(
        "性別",
        options=["総数", "男", "女"],
    )

    # 年（ドロップダウン）
    years = get_years()
    year = st.selectbox(
        "調査年",
        options=years,
    )

    st.divider()
    st.caption(
        "構成比(%) = 各労働力状態の人数 ÷ 15歳以上人口（総数）× 100　"
        "※総数には不詳を含むため、不詳回答率が高い都市部では構成比が低めに出る傾向があります。　"
        "出典：政府統計の総合窓口（e-Stat）国勢調査 時系列データ"
    )

# ── データ取得 ────────────────────────────────────────────────
df = fetch_choropleth(year=year, labor_status=labor_status, gender=gender)

if df.empty:
    st.warning("該当するデータがありません。")
    st.stop()

# ── コロプレスマップ ──────────────────────────────────────────
fig = px.choropleth_map(
    df,
    geojson=("https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"),
    locations="pref",
    featureidkey="properties.nam_ja",
    color="ratio",
    color_continuous_scale="Blues",
    range_color=(df["ratio"].min(), df["ratio"].max()),
    map_style="carto-positron",
    zoom=4.5,
    center={"lat": 38.6, "lon": 135.4},
    opacity=0.8,
    hover_name="pref",
    hover_data={
        "ratio": ":.2f",
        "value": ":,",
        "total": ":,",
        "pref": False,
    },
    labels={
        "ratio": "構成比(%)",
        "value": "人数(人)",
        "total": "15歳以上人口(人)",
    },
    title=f"{year}年　{gender}　{labor_status}　構成比(%)",
)

fig.update_layout(
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    coloraxis_colorbar=dict(
        title="構成比(%)",
        ticksuffix="%",
        thickness=15,
        len=0.6,
    ),
    height=650,
)

# クリックイベントを取得
clicked = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    key=f"map_{year}_{labor_status}_{gender}",
)

# ── サマリーテーブル ──────────────────────────────────────────
with st.expander("都道府県別データを表示"):
    display_df = (
        df[["pref", "ratio", "value"]]
        .rename(columns={"pref": "都道府県", "ratio": "構成比(%)", "value": "人数(人)"})
        .sort_values("構成比(%)", ascending=False)
        .reset_index(drop=True)
    )
    display_df.index += 1
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "構成比(%)": st.column_config.NumberColumn(format="%.2f"),
            "人数(人)": st.column_config.NumberColumn(format="%,d"),
        },
    )

# ── ドリルスルー（都道府県クリック時） ────────────────────────
st.divider()

clicked_pref = None
try:
    points = clicked.selection.points
    if points:
        clicked_pref = points[0].get("hovertext")
except Exception:
    clicked_pref = None

if clicked_pref:
    st.subheader(f"📋 {clicked_pref}　{year}年　労働力状態別構成比")
    st.caption("構成比(%) = 各労働力状態の人数 ÷ 15歳以上人口（総数）× 100")

    drill_df = fetch_drillthrough(pref=clicked_pref, year=year)

    fmt_cols = {c: "{:.2f}%" for c in drill_df.columns if c != "労働力状態"}
    st.dataframe(
        drill_df.style.format(fmt_cols),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("💡 地図の都道府県をクリックすると労働力状態別の詳細を表示します。")

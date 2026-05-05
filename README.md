# japan-census-map

国勢調査（e-Stat）データを都道府県別の構成比（%）でインタラクティブに探索できる地図アプリです。

## 記事

<!-- Zenn記事のURL（公開後に追記） -->
https://zenn.dev/（公開後に追記）

## セットアップ

```bash
uv sync
# Windows
.venv\Scripts\python -m streamlit run app.py
```

## フォルダ構成

```
japan-census-map/
├── .streamlit/
│   └── config.toml           # テーマ設定
├── data/
│   └── raw/
│       └── census_labor.csv  # ソースデータ。コードからは読み取り専用
├── src/
│   ├── db.py                 # CSV→SQLite変換
│   └── query.py              # SQLiteによるデータ取得・集計
├── app.py                    # エントリーポイント
└── pyproject.toml
```

## データソース

本リポジトリで使用したデータは、e-Stat（政府統計の総合窓口）が公開している国勢調査データです。

- 出典：政府統計の総合窓口（e-Stat） https://www.e-stat.go.jp/
- 利用規約：https://www.e-stat.go.jp/terms-of-use
- 統計名：国勢調査 時系列データ 人口の労働力状態，就業者の産業・職業
- 表番号：2
- 表題：労働力状態（3区分），男女別人口及び労働力率（15歳以上）－ 都道府県（昭和25年～令和2年）
- データセットURL：https://www.e-stat.go.jp/dbview?sid=0003412176

## ライセンス

本リポジトリのコードはMIT Licenseです。データの利用については上記e-Statの利用規約に従ってください。
# このリポジトリ向け AI エージェント・クイックスタート (laharz-arcgis-python3)

このリポジトリは、ArcGIS Pro/Spatial Analyst 上で USGS LaharZ ワークフローを Python 3 で自動化します。地理処理ツールボックス（Laharz_py.tbx）から実行する想定で、ArcGIS の `sys.argv` 形式の引数を受け取り、ラスタ/シェープファイルを読み書きして中間成果物をワークスペースに生成します。

## アーキテクチャとフロー
- エントリスクリプト:
  - `surface_hydro.py`: DEM から `(<prefix>fill, <prefix>dir, <prefix>flac, <prefix>str<Stream_Value>)` を作成。
  - `proximal_zone.py`: H/L コーンを作成（頂点: 最大標高/XY/テキスト）。線→ラスタ化し、流路との交点をテキスト/シェープに出力（`laharz_shapefiles/`）。
  - `distal_inundation.py`: 主要な氾濫シミュレーション。`<prefix>fill` 等と体積リスト・開始点を用い、断面とプラニメトリック被覆を計算。各開始点ごとにグリッド `<drainName><n>` と `.pts` ログを出力。
  - `new_stream_network.py`: 既存 `<prefix>flac` を使い、しきい値だけ変更して `<prefix>str<Stream_Value>` を再生成。
  - `merge_runs.py`: 複数ランの同体積セルを `merge_<k>` モザイクに統合。
  - `raster_to_shapefile.py`: カテゴリカル氾濫ラスタをポリゴン化（`laharz_shapefiles/`）。
- 重要な規約: DEM 由来の埋め立てラスタ名が `fill` で終わる前提で、共通プレフィックス `PreName` を推定し、`PreName + {fill, dir, flac, str}` を相互参照します。
- 配列利用: `RasterToNumPyArray` で配列化し独自走査、`NumPyArrayToRaster` で元ラスタのセルサイズ/左下を使って書き戻します。

## 実行パターン（ArcGIS Pro）
- すべて `sys.argv` 形式。典型例:
  - Surface hydrology: workspace, DEM, prefix, stream_threshold (例: 1000)
  - Proximal zone: workspace, DEM, stream raster, slope (例: 0.3), apex 選択, apex 座標ファイル, 手入力座標
  - Distal inundation: workspace, DEM（`<prefix>fill` を配列化に使用）, drain 名, volumes.txt, start_points.txt, flowType または信頼水準
- Spatial Analyst 必須: `arcpy.CheckOutExtension("Spatial")`
- 環境は入力 DEM に合わせる: `env.extent`, `env.snapRaster`, `env.cellSize`

## テキストファイル形式
- 体積ファイル: CSV または 1 行 1 値。float を丸めて使用。信頼区間モード時は先頭体積のみ利用。
- 開始点ファイル: `x,y`（投影座標）を 1 行 1 組。`distal_inundation.py` と `proximal_zone.py` で使用。
- マージリスト: マージ対象ラスタ名を 1 行 CSV（`merge_runs.py`）。

## 命名規約と出力
- 水文ラスタ: `<prefix>{fill,dir,flac,str<Stream_Value>}` をワークスペース直下に作成。
- 近傍（コーン）成果物: 一時ラスタはワークスペース、シェープは `laharz_shapefiles/`、座標は `laharz_textfiles/`。
- 遠方（氾濫）成果物: 開始点ごとにラスタ `<drainName><n>` と `.pts` ログ。セル値は断面被覆回数（背景=1）。
- マージ出力: `merge_<k>`（整数ラスタ、属性テーブル付き）。

## プロジェクト慣習と注意点
- プレフィックス推定: 入力に `<prefix>fill` を渡す前提で `PreName` を解決。誤ると付随ラスタが見つかりません。
- パスは Windows 形式で `env.workspace` 基準。`laharz_textfiles/` と `laharz_shapefiles/` が存在する前提（無ければ作成）。
- 流向コードは D8（2 の冪）。斜め/直交で断面のセル寸法（対角/幅）を切り替えます。
- 遠方計算は A(DEM), B(開始点/被覆), C(流向) を使用。下流に C で前進し、`planvals` に被覆を集計。
- 信頼区間モード: `flowType` に数値（例: `90`）を渡すと `laharz_textfiles/py_xxsecta.txt`, `py_xxplanb.txt`, `py_xxttabl.txt` を用いて上限/下限面積を導出。

## 安全に拡張するには
- 既存の環境設定・命名規約を再利用し、`env.extent/snapRaster/cellSize` を必ず入力ラスタに揃える。
- 新しいラスタ演算は `arcpy.sa`（Fill, FlowDirection, FlowAccumulation, Con, Plus, GreaterThan, Minus, Times, EucDistance, Int）を優先し、配列⇄ラスタの再サンプリング齟齬を避ける。
- `distal_inundation.py` を触る際は B 配列の意味（1=背景, >1=被覆段数）と面積/断面リストの降順並びを保持する。

## 参考になる箇所（本リポジトリ内）
- 水文生成: `surface_hydro.py` の `fillname/dirname/flacname/strname` 設定と `.save()`。
- H/L コーンと入出力: `proximal_zone.py` の `Maximum_Elevation/XY_coordinate/Textfile` 分岐と `hl_cone_*.shp`・`startpnts_*.txt`。
- 遠方アルゴリズムの肝: `distal_inundation.py` の `CalcCrossSection` と下流ループ。

## ローカル実行メモ（ツールボックス外で直実行）
- ArcGIS Pro の Python 環境（Spatial Analyst 付き）を有効化。
- 入力ラスタが命名規約に従って存在し、相互参照できることを確認。
- `laharz_textfiles` と `laharz_shapefiles` を作成済みであること。

## コミットメッセージ運用 (Conventional Commits)
AI にコミット文生成を依頼した場合は、[Conventional Commits](https://www.conventionalcommits.org/ja/v1.0.0/) 仕様をベースに常に以下 3 案を提示する: 基本 / 詳細 / 要約重視。

### フォーマット
```
<type>(<scope>): <要約>

WHY: <理由> (任意)
BEFORE: <主な変更前状態> (必要に応じ)
AFTER: <主な変更後状態> (必要に応じ)

変更点:
- <操作 + 対象 + 理由>
- ...

Refs: <関連リンクやID> (任意)
```

`変更点:` セクションは 1–2 項目でも再現性向上につながるなら付与。大量同種更新は「他 N 件同種」で集約。

### type
- feat / fix / docs / chore / refactor / style / build / perf
  (本文で意味が曖昧な場合は別案を提示)

### scope（任意）
- article / meta / tags / automation

### 要約規則
- 50文字以内 / 文末「。」なし / 操作 + 対象 + 目的

### 例（詳細案）
```
docs(meta): コミット規約を再構成し簡潔化

WHY: 旧ガイドが冗長で参照コストが高かったため。
AFTER: 3案出力と詳細列挙を標準化。

変更点:
- 旧コミット節を全面削除
- 再構成した最小コアルールを追加
- 3種(基本/詳細/要約) 提示方針を明文化
```

### 3 案出力方針
1. 基本: 要約 + WHY (必要最小)
2. 詳細: WHY/AFTER + `変更点:` 箇条書き（標準）
3. 要約重視: subject 強調 / 本文最小化

差分が極小（1行スペース調整等）の場合のみ 1 案 (chore/style) でもよいが、その判断はユーザー指示があるときに限る。

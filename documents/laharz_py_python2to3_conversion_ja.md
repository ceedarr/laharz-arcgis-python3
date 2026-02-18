2025年8月29日 杉村

## 本ファイルの目的

LAHARZ_py使用に際して発生したエラーへの対処内容を記す。

注意:
本修正は、ArcGIS上でLAHARZ_pyプラグイン「create surface hydrology rasters」「generate new stream network」「hazard zone proximal」「laharz distal zones」を使用したときに発生したエラーに対処したものです。
そのため、未使用の「laharz distal zones with conf levels」「merge rasters by volume」「raster to shapefile」で問題が発生するかは分かりません。必要に応じて修正してください。

## 背景

「LAHARZ」は、Schilling (2014) が公開したソフトウェアです。USGSのWebサイト (https://pubs.usgs.gov/of/2014/1073/) からダウンロードできます。LAHARZはラハール総流量と断面積、総流量と表面積のスケーリング解析に基づいており、入力された地形データ (DEM) 上を、流路の全ての断面積が全て同じAという値に、流下範囲の表面積がBという値になるように流下範囲を計算します。
詳細なアルゴリズムを知るには Iverson et al. (1998) やSchilling (1998; 2014) を読むか、プログラム本体を読むことを推奨します。

上記で述べた断面積A、表面積Bは、A=0.05×体積^(2/3); B=200×体積^(2/3)と求められています (Iverson et al., 1998)。
補足: また2025年時点では、岩屑なだれ、火砕流 (PFz: pyloclastic flow z) などにおいても異なる係数が明らかになっています (Schilling, 2014; Widiwijayanti et al., 2009)。

## 本文書がコード修正に使用した環境

- 作業環境:
    - Windows 11
    - ArcGIS Pro 3.4
    - (VSCodeかその他のコードエディタ)

## プログラムの修正

USGSのWebサイト (https://pubs.usgs.gov/of/2014/1073/) からLAHARZ_py ("LAHARZ_py_example.zip") をダウンロードして展開しておく。

LAHARZ_pyはPythonバージョン2で動作するよう開発されたが、最新のArcGIS ProバージョンはPython3対応でありPython2は利用できない(と思われる)。
このままだとバージョン違い由来のエラーが発生する(した)ので、修正した内容を下記に列挙する。

本文書は修正のためにVSCode (コードエディタ) の文字置換機能を利用した。
文字置換参考: https://www.chihayafuru.jp/tech/index.php/archives/2294, https://zenn.dev/posita33/articles/vscode_multifiles_find_and_replace, https://iroirodesignlab.com/2023/06/06/837/, https://zenn.dev/uniformnext/articles/0edccd0c681474

1. print関数の構文

修正内容:
LAHARZ_py内の全てのprint関数について、print関数の引数をかっこで囲う
要修正ファイルは"distal_inundation.py"、"new_stream_network.py"、"surface_hydro.py"

修正例:
誤 Python2）print "Bad flow direction ", currFlowDir
正 Python3）print("Bad flow direction ", currFlowDir)

- 正規表現 (VS Code)
    search: "print (.+)"
    replace: "print($1)"

2. 「等しくない」演算子

修正内容:
「等しくないならTrueを返す」意味の演算子の記法を修正する
要修正ファイルは"distal_inundation.py"、"merge_runs.py"、"proximal_zone.py"

修正例:
誤 Python2）if aline.find(',') <> -1:  # if it does have a ','
正 Python3）if aline.find(',') != -1:  # if it does have a ','

- 正規表現 (VS Code)
    search: "<>"
    replace: "!="

3. 時刻取得関数

修正内容:
"time.clock()"関数を"time.process_time()"関数に変更する
Python3のtimeライブラリにclock関数は存在しない
要修正ファイルは"distal_inundation.py"、"merge_runs.py"、"raster_to_shapefile.py"

修正例:
誤 Python2）starttimetot = time.clock()  # calculate time for program run
正 Python3）starttimetot = time.process_time()  # calculate time for program run

- 正規表現 (VS Code)
    search: "time\.clock"
    replace: "time.process_time"

4. ファイル読み込み関数

修正内容:
"file()"関数を"open()"関数に変更する
Python3では関数名がfileからopenに変更されている
要修正ファイルは"distal_inundation.py"

修正例:
誤 Python2）outfile = file(ptsfilename, "a")
正 Python3）outfile = open(ptsfilename, "a")

- 正規表現 (VS Code)
    search: "file\("
    replace: "open("

5. open()関数のBOM対応

修正内容：
Windows11日本語環境で作成したテキストファイルに起因するUnicodeErrorへの対処。
UTF-8(BOM付き/無し)が混在するテキストファイル（開始点座標、体積リスト）の読み書きで、
先頭の不可視文字（BOM）や文字化けを防ぐため、テキストモードの open() に encoding="utf_8_sig" を付与する。
要修正ファイルは"distal_inundation.py"、"merge_runs.py"、"proximal_zone.py"

修正例:
誤）outfile = open(ptsfilename, "a")
正）outfile = open(ptsfilename, "a", encoding="utf_8_sig")

- 正規表現 (VS Code)
    search: "open\((.+[r|a|w]["|'])\)"
    replace: "open($1, encoding="utf_8_sig")"

6. arcpy環境変数記法

修正内容：
arcpyライブラリのenv

要修正ファイルは"new_stream_network.py"



7. 係数変更方法の明確化

変更内容：
LaharZ実行時の係数を簡単に指定できるようにするために、"coefficient_setting.py"という新しいPythonファイルを作成し、そこに係数を定義する方法を採用する。

主な変更点（実装）:
- `coefficient_setting.py` を追加し、係数（A, B）を1か所で管理する構成に変更した。
- `distal_inundation.py` は固定値の分岐（Lahar=0.05/200 など）ではなく、`COEFFICIENTS` から `flowType` ごとに係数を参照して計算するようになった。
- 係数例や候補値は `coefficient_catalogue.txt` でも確認できるようにした。

係数調整時にコード本体（`distal_inundation.py`）を編集する必要がなくなり、設定ファイル側の更新だけで運用できるようにしました。



8. `hazard zone proximal` の中間ラスタを GeoTIFF (`.tif`) に統一

変更内容：
`hazard zone proximal` 実行時の中間ラスタについて、拡張子なし（ESRI GRID想定）で保存していた処理を、GeoTIFF（`.tif`）で保存する形に変更した。
これにより、中間ファイルの扱いを明示的にし、後続処理（ラスタ結合・ポリゴン変換・一時ファイル削除）まで同じ形式で統一した。

この変更の動機は、1mメッシュ実行時に `proximal_zone.py` の保存処理付近で `RuntimeError: Invalid pointer` が発生したことへの対処。

主な変更点（実装）:
- `proximal_zone.py` において、`xhltemp` を `xhltemp.tif` として保存・参照するように変更した。
- Textfile 分岐で作成される一時ラスタ（`hl_cone_g2{i}.tif`, `grid1.tif`, `temp.tif`, `xhltempx.tif`）を `.tif` 形式へ統一した。
- `RasterToPolygon_conversion` の入力ラスタを `xhltemp.tif` に変更した。
- `.tif` 化した一時ファイルに対応する削除処理を追加した。

この変更により、`hazard zone proximal` の中間ラスタ処理が一貫した形式で運用できるようになった。


要修正事項 以上
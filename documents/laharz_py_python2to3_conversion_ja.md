2025年8月29日 杉村

## 本ファイルの目的

LAHARZ_py使用に際して発生するエラーを解消する。

注意:
本修正は、ArcGIS上でLAHARZ_pyプラグイン「create surface hydrology rasters」「generate new stream network」「hazard zone proximal」「laharz distal zones」を使用したときに発生したエラーに対処したものです。
そのため、未使用の「laharz distal zones with conf levels」「merge rasters by volume」「raster to shapefile」で問題が発生するかは分かりません。必要に応じて修正してください。

## 背景

「LAHARZ」は、Schilling (2014) が公開したソフトウェア。USGSのWebサイト (https://pubs.usgs.gov/of/2014/1073/) からダウンロードできる。
LAHARZは、「ラハール総体積の2/3乗とラハール流路断面積、ラハール総体積の2/3乗とラハール表面積のそれぞれに比例関係が成り立つ」仮定に基づいており、
入力された地形データ (DEM) 上を、流下開始地点から下流に向かって「地形 (DEMの各グリッド) を充填」するように氾濫エリアを計算する。
詳細なアルゴリズムを知るには Iverson et al. (1998) やSchilling (1998; 2014) を読むか、プログラム本体を読むことを推奨。

上記で述べた「比例関係」は、断面積=0.05×体積^(2/3); 表面積=200×体積^(2/3)と求められている (Iverson et al., 1998)。
補足: また2025年時点では、岩屑なだれ、火砕流 (PFz: pyloclastic flow z) などにおいても比例係数が明らかになっている (Schilling, 2014; Widiwijayanti et al., 2009)。

本ファイル作成時点の課題として、「LAHARZでラハールを計算する際に流動特性に基づき異なる比例係数を適用すべきか」という点に取り組んでいる。
そのためにLAHARZを使う必要があり本ファイル作成に至った。

## 本文書の前提

- 作業環境:
    - Windows 11
    - ArcGIS Pro 3.4
    - (VSCodeかその他のコードエディタ)

## プログラムの修正

USGSのWebサイト (https://pubs.usgs.gov/of/2014/1073/) からLAHARZ_py ("LAHARZ_py_example.zip") をダウンロードして展開しておく。

LAHARZ_pyはPythonバージョン2で動作するよう開発されたが、最新のArcGIS ProバージョンはPython3に対応している。
このままだとバージョン違い由来のエラーが発生する(した)ので、修正すべき内容を下記に列挙する。

また、修正忘れを避けるために、VSCodeなどのコードエディタで文字検索機能を利用することを推奨。
参考: https://www.chihayafuru.jp/tech/index.php/archives/2294, https://zenn.dev/posita33/articles/vscode_multifiles_find_and_replace, https://iroirodesignlab.com/2023/06/06/837/, https://zenn.dev/uniformnext/articles/0edccd0c681474

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



7?. エンコード処理 (日本語環境のみ必要な修正)

修正内容:
+演算子と"\\"を使ったパス結合をos.path.join()を使ったものに変更する
日本語のPC環境/プロジェクト名/ディレクトリ名のいずれかが原因のため、utf-8とshift-jis混在を解消する。
英語 (アルファベット、数字など)のみの環境の場合この修正は不要
要修正ファイルは"distal_inundation.py"

修正対象: "distal_inundation.py"の1591行目
```python
myRaster.save(env.workspace + "\\" + str(drainName) + str(blcount))
```
これを下記に書き換える
```python
# ======== fixing for encode flexibility 2025-09-09 Kazuki
# myRaster.save(env.workspace + "\\" + str(drainName) + str(blcount))       # this is original code, which cause error when mixing utf-8 and shift-jis (japanese encode)

myRaster.save(os.path.join(env.workspace, (str(drainName) + str(blcount)))) # no error even if mixing

# Alternative using pathlib (optional):
# import pathlib
# myRaster.save(str(pathlib.Path(env.workspace) / (str(drainName) + str(blcount)))) # also no error even if mixing but you need to use "pathlib" library additionally
# ======== end of fixing
```


要修正事項 以上
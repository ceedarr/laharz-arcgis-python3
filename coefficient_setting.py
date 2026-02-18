# このファイルの使い方は末尾"""以下参照

# A: 断面積の係数C_A (LaharZ式: A = C_A * V^(2/3))
# B: 表面積の係数C_B (LaharZ式: B = C_B * V^(2/3))
COEFFICIENTS = {
    'Lahar': {
        "A": 0.05,
        "B": 200
    },
    'Debris_Flow': {
        "A": 0.1,
        "B": 20
    },
    'Rock_Avalanche': {
        "A": 0.2,
        "B": 20
    }
}

"""
2026年2月18日
このPythonファイルは、LaharZ実行時の係数を指定するためのものです。
辞書の変数である"COEFFICIENTS"に、LaharZ実行に用いる係数を入力してください。

現状、LaharZのツールボックスにおいて、'Lahar', 'Debris_Flow', 'Rock_Avalanche'の3つのモード名が定義されています。これらの名前は変更できず、追加もできません。
そのため、例えば「粘着性ラハールと非粘着性ラハールそれぞれの係数を使ってLaharZを実行したい」という場合は、以下のように"COEFFICIENTS"を定義してください。

COEFFICIENTS = {
    'Lahar': { # 粘着性ラハールの係数
        "A": 0.329, # 例
        "B": 154    # 例
    },
    'Debris_Flow': { # 非粘着性ラハールの係数
        "A": 0.051, # 例
        "B": 200    # 例
    }
}
"""
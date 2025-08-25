#!/usr/bin/env python3
import sys
import os

# コマンドライン引数からファイルパスを取得
file_path = sys.argv[1] if len(sys.argv) > 1 else ''

# ファイル拡張子を取得
file_ext = os.path.splitext(file_path)[1] if file_path else ''

# .jcファイルかどうかをチェック
if file_ext == '.jc':
    print("✅ JCLファイルが選択されています。実行を開始します...")
    sys.exit(0)  # 成功
else:
    print("❌ エラー: JCLファイル(.jc)を選択してください。")
    print(f"   選択されたファイル: {file_path}")
    print(f"   検出された拡張子: {file_ext}")
    sys.exit(1)  # 失敗

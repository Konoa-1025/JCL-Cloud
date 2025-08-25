# transpiler.py (最終版 - すべての既知のコンパイルエラー対応)

import re
import sys # sysモジュールを追加

KEYWORDS = {
    # 制御構文 (長いキーワードから順に定義し、部分マッチ問題を回避)
    "そうでなければもし": "else if", # 'else if'に修正
    "そうでなければ": "else",
    "ファイルフォーマット出力": "fprintf", 
    "ファイルフォーマット入力": "fscanf",  
    "ファイルフラッシュ": "fflush",
    "文字列文字数": "strlen",  
    "文字列複製": "strcpy",   
    "文字列結合": "strcat",   
    "ファイル出力": "fprintf",
    "ファイル入力": "fscanf",
    "ファイル設定": "fseek", 
    "ファイル閉じる": "fclose",
    "ファイル開く": "fopen",
    "メモリ確保": "malloc",   
    "メモリ解放": "free",
    "乱数初期化": "srand",
    "乱数生成": "rand",
    "現在時刻": "time",
    "時刻変換": "ctime",
    "ローカル時刻": "localtime",
    "時刻フォーマット": "strftime",
    "文字入力": "getchar",
    "繰り返し": "for",
    "続行": "continue",
    "抜ける": "break",
    "主関数": "int main", # main関数にintの戻り値を追加
    "時刻型": "time_t", # 時刻を扱う型
    "整数型": "int",
    "実数型": "double", # 実数型はdoubleにマッピング（高精度を推奨）
    "文字型": "char",
    "選択": "switch",
    "戻る": "return",
    "出力": "printf",
    "表示": "printf",  # 追加: 表示もprintfにマッピング
    "入力": "scanf",
    "もし": "if",
    "間": "while",
}

# 日本語変数名をC言語の変数名にマッピング (必要に応じて追加してください)
JAPANESE_VARIABLES = {
    "名前": "name",
    "年齢": "age",
    "身長": "height",
    "メッセージ": "message",
    "結果コード": "result_code",
    # main.jc で使われている変数を追加
    "gk": "gk", # これらの変数はそのまま使う場合
    "m": "m",
    "s": "s",
    "g": "g",
    "gh": "gh",
    "h": "h",
    "n": "n",
    "text": "text"
}


def transpile_jc_to_c(jc_text: str) -> str:
    c_lines = []

    for line_num, line in enumerate(jc_text.splitlines()):
        original_indent = re.match(r"^\s*", line).group(0)
        trimmed_line = line.strip()

        if not trimmed_line:
            c_lines.append(line)
            continue

        processed_line = trimmed_line

        # --- プリプロセッサディレクティブの処理（JCL側で #, ; およびコメントを考慮） ---
        is_preprocessor_directive = False
        
        # 行末のセミコロンと行コメントを処理し、ディレクティブ部分のみを抽出
        # まずコメント部分を除去
        clean_directive_line = trimmed_line.split('//', 1)[0].strip()
        # 次に末尾のセミコロンを除去
        if clean_directive_line.endswith(';'):
            clean_directive_line = clean_directive_line[:-1].strip()
        
        # JCL: 組み込む<ヘッダー名>
        if clean_directive_line.startswith("組み込む<") and clean_directive_line.endswith(">"):
            include_content = clean_directive_line[len("組み込む<") : -1] # <...> の中身を抽出
            
            # JCLヘッダー名をCのヘッダー名にマッピング
            c_header_name = {
                "標準入出力": "stdio.h",
                "メモリ管理": "stdlib.h",
                "文字列操作": "string.h",
                "時間操作": "time.h",
            }.get(include_content, include_content) # マッピングがなければそのまま使用
            
            processed_line = f"#include <{c_header_name}>"
            c_lines.append(original_indent + processed_line)
            is_preprocessor_directive = True
        
        # JCL: 定義 マクロ名 値
        elif clean_directive_line.startswith("定義 "): 
            define_content = clean_directive_line[len("定義 "):] # "定義 "以降の文字列を抽出
            processed_line = f"#define {define_content}"
            c_lines.append(original_indent + processed_line)
            is_preprocessor_directive = True
        
        if is_preprocessor_directive:
            continue # プリプロセッサディレクティブはここで処理完了し、次の行へ

        # --- 通常の行の処理 (プリプロセッサディレクティブでなかった場合) ---

        # Step 1: 文字列リテラルを一時的にプレースホルダーに置換
        string_literals_raw = [] 
        def replace_string_with_placeholder(match):
            string_content = match.group(1) 
            string_literals_raw.append(string_content)
            return f"__STRING_PLACEHOLDER_{len(string_literals_raw) - 1}__"

        processed_line_after_string_hiding = re.sub(r'"((?:[^"\\]|\\.)*)"', replace_string_with_placeholder, processed_line)

        # Step 1.5: 日本語変数名をC言語変数名に置換 (単語の境界を考慮)
        # キーを降順にソートして長い変数名が先にマッチするようにする（念のため）
        processed_line_after_var_replace = processed_line_after_string_hiding
        sorted_japanese_variables = sorted(JAPANESE_VARIABLES.items(), key=lambda item: len(item[0]), reverse=True)
        for jp_var, c_var in sorted_japanese_variables:
            # 正規表現で単語の境界(\b)を使って、完全な単語としてマッチさせる
            # jp_varに特殊文字が含まれる可能性を考慮しre.escapeを使用
            processed_line_after_var_replace = re.sub(r'\b' + re.escape(jp_var) + r'\b', c_var, processed_line_after_var_replace)


        # Step 2: JCLキーワードをCの対応物に置換 (longest match firstはKEYWORDSの定義順で対応)
        processed_line_after_keyword_replace = processed_line_after_var_replace
        # KEYWORDS辞書が定義順を保持するので、そのままループ
        for jp_keyword, c_equivalent in KEYWORDS.items():
            # フォーマット指定子などは文字列内で処理されるためスキップ
            if jp_keyword in ["絶対l型整数", "絶対h型整数", "l型整数16進", "l型整数8進", 
                              "l型整数", "h型整数", "絶対整数", "整数16進", "整数8進", 
                              "文字列", "実数", "文字", "整数", "改行" # フォーマット指定子など
                             ]:
                continue
            # 変数名と重ならないようにキーワードは単語境界なしでreplace
            # ただし、現状のキーワードは単語なのでこれでOK
            processed_line_after_keyword_replace = processed_line_after_keyword_replace.replace(jp_keyword, c_equivalent)
        
        # Step 3: 特定の関数引数の型キャストを処理 (例: strlenの出力)
        processed_line_after_func_cast = re.sub(r"strlen\((.*?)\)", r"(int)strlen(\1)", processed_line_after_keyword_replace)

        # Step 4: 文字列リテラルを再挿入し、Cのフォーマット指定子に変換
        final_processed_line = processed_line_after_func_cast
        
        string_literals_processed = []
        for s_val_raw in string_literals_raw:
            s_val = s_val_raw 

            s_val = s_val.replace("改行", "\\n")   
            
            # 変換指定子を優先的に置換（長いものから順に）
            s_val = s_val.replace("絶対l型整数", "%lu")
            s_val = s_val.replace("絶対h型整数", "%hu")
            s_val = s_val.replace("l型整数16進", "%lx")
            s_val = s_val.replace("l型整数8進", "%lo")
            s_val = s_val.replace("l型整数", "%ld")
            s_val = s_val.replace("h型整数", "%hd")
            s_val = s_val.replace("絶対整数", "%u")
            s_val = s_val.replace("整数16進", "%x")
            s_val = s_val.replace("整数8進", "%o")
            s_val = s_val.replace("文字列", "%s")   
            s_val = s_val.replace("整数", "%d")     

            # 実数型の入出力はprintfとscanfでフォーマット指定子が異なるため、
            # 現在の行が"出力"か"入力"かを判断して変換
            if trimmed_line.startswith("出力(") or trimmed_line.startswith("表示("): # コンテキスト判断のためにtrimmed_lineを使用
                s_val = s_val.replace("実数", "%f")     # printfではdoubleも%f
                s_val = s_val.replace("文字", "%c")     # 出力時は通常の%c
            elif trimmed_line.startswith("入力("): # コンテキスト判断のためにtrimmed_lineを使用
                s_val = s_val.replace("実数", "%lf")    # scanfでdoubleは%lf
                s_val = s_val.replace("文字", " %c")    # 文字入力時は前に空白を入れてバッファクリア
            
            string_literals_processed.append(f'"{s_val}"') 

        for i in range(len(string_literals_raw) - 1, -1, -1):
            final_processed_line = final_processed_line.replace(f"__STRING_PLACEHOLDER_{i}__", string_literals_processed[i], 1)
        
        processed_line = final_processed_line 

        # Step 5: セミコロンの自動挿入とfflush(stdout)
        add_semicolon = True
        control_flow_keywords_no_semicolon = ["if", "else", "for", "while", "switch", "do"] 
        
        if processed_line.startswith("#"): 
            add_semicolon = False
        elif processed_line.endswith("{") or processed_line.endswith("}"): 
            add_semicolon = False
        elif processed_line.endswith("},"): # 配列初期化子でのセミコロン防止を追加
            add_semicolon = False
        elif processed_line.endswith(";"): 
            add_semicolon = False
        elif any(processed_line.startswith(kw) for kw in control_flow_keywords_no_semicolon):
            add_semicolon = False
        
        if add_semicolon:
            processed_line += ";"
        
        # 行を追加（printf、int main、その他で分岐）
        if processed_line.startswith("printf("):
            c_lines.append(original_indent + processed_line)
            c_lines.append(original_indent + "fflush(stdout); //JCLによって自動生成されました")
        elif processed_line.startswith("int main("):
            c_lines.append(original_indent + processed_line)
            c_lines.append(original_indent + "    setlocale(LC_ALL, \"ja_JP.UTF-8\");//JCLによって自動生成されました")
        else:
            c_lines.append(original_indent + processed_line)

    c_code = '// This code was generated by JapaneseC Language Transpiler.\n'
    # 必要なCヘッダーファイルを明示的に含める（JCLの組み込むに依存せず常に追加）
    # これにより、JCL側で「組み込む」がなくてもstdio.hなどが含まれることを保証
    c_code += '#include <stdio.h>\n'
    c_code += '#include <stdlib.h>\n'
    c_code += '#include <string.h>\n'
    c_code += '#include <locale.h>//JCLによって自動生成されました\n\n'

    c_code += '\n'.join(c_lines)
    return c_code

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess, tempfile, os, textwrap, shutil

# JCLトランスパイラをインポート
from transpiler import transpile_jc_to_c

app = FastAPI()

# 必要に応じてフロントのドメインを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunReq(BaseModel):
    code: str

def jcl_to_c(jcl_code: str) -> str:
    """
    JCLコードをC言語コードにトランスパイルする
    完全なJCLトランスパイラを使用
    """
    try:
        return transpile_jc_to_c(jcl_code)
    except Exception as e:
        # トランスパイルエラーの場合、エラー情報を含むCコードを生成
        error_c_code = f'''
#include <stdio.h>
int main() {{
    printf("JCLトランスパイルエラー: {str(e)}\\n");
    return 1;
}}
'''
        return error_c_code

@app.post("/run")
def run(req: RunReq):
    work = tempfile.mkdtemp(prefix="jcl_")
    try:
        c_path = os.path.join(work, "out.c")
        exe_path = os.path.join(work, "a.out")
        open(c_path, "w").write(jcl_to_c(req.code))

        # コンパイル
        compiler_cmd = ["gcc", c_path, "-o", exe_path]
        r = subprocess.run(compiler_cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return {"ok": False, "stage":"compile", "stdout": r.stdout, "stderr": r.stderr}

        # 実行（2秒タイムアウト）
        r2 = subprocess.run([exe_path], capture_output=True, text=True, timeout=2)
        return {"ok": r2.returncode == 0, "stage":"run", "stdout": r2.stdout, "stderr": r2.stderr}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "run", "stdout": "", "stderr": "Execution timed out (2 seconds)"}
    except Exception as e:
        return {"ok": False, "stage": "error", "stdout": "", "stderr": f"Error: {str(e)}"}
    finally:
        shutil.rmtree(work, ignore_errors=True)

@app.get("/")
def health_check():
    return {"message": "JCL Cloud API is running!", "status": "ok"}

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import subprocess, tempfile, os, textwrap, shutil

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
    # TODO: のりのJCLトランスパイラで置き換える
    # いったんダミー（最低限の通し確認用）
    return textwrap.dedent("""\
    #include <stdio.h>
    int main(){ printf("Hello from JCL!\\n"); return 0; }
    """)

@app.post("/run")
def run(req: RunReq):
    work = tempfile.mkdtemp(prefix="jcl_")
    try:
        c_path = os.path.join(work, "out.c")
        exe_path = os.path.join(work, "a.out")
        open(c_path, "w").write(jcl_to_c(req.code))

        # コンパイル（Windows環境ではgccまたはclangを使用）
        # Windowsの場合、.exeを追加
        if os.name == 'nt':
            exe_path = exe_path + ".exe"
            compiler_cmd = ["gcc", c_path, "-o", exe_path]
        else:
            compiler_cmd = ["tcc", c_path, "-o", exe_path]
        
        r = subprocess.run(compiler_cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return {"ok": False, "stage":"compile", "stdout": r.stdout, "stderr": r.stderr}

        # 実行（2秒タイムアウト）
        # WindowsとLinuxで異なるタイムアウト方法を使用
        if os.name == 'nt':
            # Windows環境では、subprocess.run自体のtimeoutを使用
            r2 = subprocess.run([exe_path], capture_output=True, text=True, timeout=2)
        else:
            # Linux環境では、timeoutコマンドを使用
            r2 = subprocess.run(["timeout", "2s", exe_path], capture_output=True, text=True)
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

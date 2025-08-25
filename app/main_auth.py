from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import subprocess, tempfile, os, textwrap, shutil
import jwt
import hashlib
from datetime import datetime, timedelta
import os
from openai import OpenAI

# JCLトランスパイラをインポート
from transpiler import transpile_jc_to_c

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# セキュリティ設定
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ホワイトリスト（環境変数から取得）
WHITELIST_EMAILS = os.getenv("WHITELIST_EMAILS", "norifumi.kondo.it@gmail.com,studio.delta.tester1@gmail.com").split(",")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "jcl2025")

class LoginRequest(BaseModel):
    email: str
    password: str

class RunReq(BaseModel):
    code: str
    input_data: Optional[List[str]] = None

class AIRequest(BaseModel):
    prompt: str
    code: Optional[str] = None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="無効なトークンです")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="無効なトークンです")

@app.post("/login")
def login(request: LoginRequest):
    """簡易ログイン - ホワイトリストチェック + パスワード"""
    
    # ホワイトリストチェック
    if request.email not in WHITELIST_EMAILS:
        raise HTTPException(status_code=403, detail="アクセス許可されていないメールアドレスです")
    
    # 簡易パスワードチェック
    if request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="パスワードが正しくありません")
    
    # トークン生成
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_email": request.email
    }

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
def run(req: RunReq, current_user: str = Depends(verify_token)):
    """認証が必要なJCL実行エンドポイント（scanf対応）"""
    work = tempfile.mkdtemp(prefix="jcl_")
    try:
        c_path = os.path.join(work, "out.c")
        exe_path = os.path.join(work, "a.out")
        
        # JCLからCにトランスパイル
        c_code = jcl_to_c(req.code)
        
        # 生成されたCコードをファイルに書き込み
        open(c_path, "w").write(c_code)

        # コンパイル
        compiler_cmd = ["gcc", c_path, "-o", exe_path]
        r = subprocess.run(compiler_cmd, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return {
                "ok": False, 
                "stage": "compile", 
                "stdout": r.stdout, 
                "stderr": r.stderr,
                "user": current_user
            }

        # 実行（scanf対応）
        stdin_input = None
        if req.input_data:
            stdin_input = "\n".join(req.input_data) + "\n"
        
        r2 = subprocess.run([exe_path], 
                          capture_output=True, 
                          text=True, 
                          timeout=2,
                          input=stdin_input)
        return {
            "ok": r2.returncode == 0, 
            "stage": "run", 
            "stdout": r2.stdout, 
            "stderr": r2.stderr,
            "user": current_user
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stage": "run", "stdout": "", "stderr": "Execution timed out (2 seconds)"}
    except Exception as e:
        return {"ok": False, "stage": "error", "stdout": "", "stderr": f"Error: {str(e)}"}
    finally:
        shutil.rmtree(work, ignore_errors=True)

@app.get("/")
def health_check():
    return {"message": "JCL Cloud API is running!", "status": "ok", "auth": "required"}

@app.get("/status")
def auth_status(current_user: str = Depends(verify_token)):
    return {"message": "認証済み", "user": current_user, "status": "authenticated"}

# AI機能エンドポイント
@app.post("/ai/generate")
def ai_generate(req: AIRequest, current_user: str = Depends(verify_token)):
    """AIコード生成エンドポイント"""
    try:
        # OpenAI APIキーの設定（環境変数から取得）
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {"ok": False, "error": "OpenAI API key not configured"}
        
        client = OpenAI(api_key=api_key)
        
        system_prompt = """あなたはJCL（Japanese Coding Language）のエキスパートです。
JCLの文法規則:
- 主関数() { ... } でプログラムを開始
- 表示("テキスト改行") で出力
- 整数型、文字列型 で変数宣言
- 入力("整数", &変数) でscanf相当
- 繰り返し(初期化; 条件; 更新) { ... } でfor文
- もし(条件) { ... } でif文
- 戻る 値; でreturn文

ユーザーの要求に基づいてJCLコードを生成してください。"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        generated_code = response.choices[0].message.content
        
        return {
            "ok": True,
            "code": generated_code,
            "user": current_user
        }
        
    except Exception as e:
        return {"ok": False, "error": f"AI生成エラー: {str(e)}"}

@app.post("/ai/explain")
def ai_explain(req: AIRequest, current_user: str = Depends(verify_token)):
    """AIコード解説エンドポイント"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {"ok": False, "error": "OpenAI API key not configured"}
        
        if not req.code:
            return {"ok": False, "error": "解説するコードが指定されていません"}
        
        client = OpenAI(api_key=api_key)
        
        system_prompt = """あなたはJCL（Japanese Coding Language）のエキスパートです。
提供されたJCLコードを日本語で分かりやすく解説してください。
- 各行の動作を説明
- 変数の役割を説明
- プログラム全体の流れを説明
- 初心者にも理解しやすいように丁寧に解説"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"以下のJCLコードを解説してください:\n\n{req.code}"}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content
        
        return {
            "ok": True,
            "explanation": explanation,
            "user": current_user
        }
        
    except Exception as e:
        return {"ok": False, "error": f"AI解説エラー: {str(e)}"}

@app.post("/ai/optimize")
def ai_optimize(req: AIRequest, current_user: str = Depends(verify_token)):
    """AIコード最適化エンドポイント"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            return {"ok": False, "error": "OpenAI API key not configured"}
        
        if not req.code:
            return {"ok": False, "error": "最適化するコードが指定されていません"}
        
        client = OpenAI(api_key=api_key)
        
        system_prompt = """あなたはJCL（Japanese Coding Language）のエキスパートです。
提供されたJCLコードを最適化し、改善提案を行ってください。
- より効率的なアルゴリズム
- より読みやすいコード構造
- パフォーマンス改善
- ベストプラクティスの適用
最適化されたコードと改善点の説明を提供してください。"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"以下のJCLコードを最適化してください:\n\n{req.code}"}
            ],
            max_tokens=800,
            temperature=0.3
        )
        
        optimization = response.choices[0].message.content
        
        return {
            "ok": True,
            "optimization": optimization,
            "user": current_user
        }
        
    except Exception as e:
        return {"ok": False, "error": f"AI最適化エラー: {str(e)}"}

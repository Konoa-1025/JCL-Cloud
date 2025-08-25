# JCL Cloud API

日本語で書けるプログラミング言語「JCL」をクラウドで実行できるAPIサービスです。

## 概要

JCL（Japanese Coding Language）をWebAPIとして提供し、ブラウザからJCLコードを実行できるクラウドサービスです。

## 機能

- JCLコードをC言語に変換（トランスパイル）
- リアルタイムでのコンパイル・実行
- セキュアな実行環境（タイムアウト制御）
- REST API経由でのアクセス

## API エンドポイント

### POST /run

JCLコードを実行します。

**リクエスト:**
```json
{
  "code": "主関数{ 表示(\"Hello, World!\"); 戻る; }"
}
```

**レスポンス:**
```json
{
  "ok": true,
  "stage": "run",
  "stdout": "Hello, World!\n",
  "stderr": ""
}
```

## ローカル開発

### Dockerを使用する場合

```bash
docker build -t jcl-cloud .
docker run --rm -p 8080:8080 jcl-cloud
```

### Python環境で直接実行する場合

```bash
pip install -r requirements.txt
cd app
uvicorn main:app --host 0.0.0.0 --port 8080
```

## テスト

```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"code":"主関数{ 表示(\"やっほー\\n\"); 戻る; }"}'
```

## デプロイ

### Renderへのデプロイ

1. GitHubリポジトリにプッシュ
2. Renderダッシュボードで「New Web Service」を選択
3. リポジトリを接続
4. 自動でDockerが検出され、デプロイが開始されます

## 今後の拡張予定

- [ ] JCLトランスパイラの本格実装
- [ ] Webエディタの追加
- [ ] エラーメッセージの日本語化
- [ ] サンプルコード集の追加
- [ ] セキュリティの強化（nsjail等）

## JCLについて

JCLは日本語でプログラミングができる教育向け言語です。
詳細は以下を参照してください：

- [VS Code拡張](https://marketplace.visualstudio.com/items?itemName=Studio-Delta.japanese-c-language)
- [JCL Engine](https://github.com/Konoa-1025/JCL-Engine)

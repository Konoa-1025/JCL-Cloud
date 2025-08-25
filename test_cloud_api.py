import requests
import json

def test_cloud_api():
    base_url = "https://jcl-cloud.onrender.com"
    
    print("🚀 JCL Cloud API テスト開始")
    print(f"URL: {base_url}")
    print("=" * 50)
    
    # 1. ヘルスチェック
    print("1. ヘルスチェック...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ ステータス: {response.status_code}")
        print(f"✅ レスポンス: {response.json()}")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print("\n" + "=" * 50)
    
    # 2. JCLコード実行テスト
    print("2. JCLコード実行テスト...")
    test_cases = [
        {
            "name": "基本的なHello World",
            "code": "主関数{ 表示(\"Hello from JCL Cloud!\"); 戻る; }"
        },
        {
            "name": "日本語メッセージ",
            "code": "主関数{ 表示(\"こんにちは、JCLクラウド！\"); 戻る; }"
        },
        {
            "name": "複数行出力",
            "code": "主関数{ 表示(\"1行目\\n\"); 表示(\"2行目\\n\"); 戻る; }"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"コード: {test['code']}")
        
        try:
            response = requests.post(
                f"{base_url}/run",
                json={"code": test['code']},
                timeout=10
            )
            
            print(f"ステータス: {response.status_code}")
            result = response.json()
            print(f"成功: {result.get('ok', False)}")
            print(f"ステージ: {result.get('stage', 'unknown')}")
            print(f"出力: {repr(result.get('stdout', ''))}")
            if result.get('stderr'):
                print(f"エラー: {result.get('stderr')}")
                
        except Exception as e:
            print(f"❌ リクエストエラー: {e}")
    
    print("\n🎉 テスト完了！")

if __name__ == "__main__":
    test_cloud_api()

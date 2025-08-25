import requests
import json

def test_real_jcl():
    base_url = "http://127.0.0.1:8080"  # ローカルテスト用
    # base_url = "https://jcl-cloud.onrender.com"  # 本番用
    
    print("🔥 本格JCLトランスパイラ テスト開始")
    print("=" * 60)
    
    # 実際のJCLコードでテスト
    test_cases = [
        {
            "name": "基本的なHello World (JCL)",
            "code": '''主関数() {
    表示("Hello from JCL!改行");
    戻る 0;
}'''
        },
        {
            "name": "変数と計算 (JCL)",
            "code": '''主関数() {
    整数型 a = 10;
    整数型 b = 20;
    表示("a + b = 整数改行", a + b);
    戻る 0;
}'''
        },
        {
            "name": "日本語変数名 (JCL)",
            "code": '''主関数() {
    整数型 年齢 = 25;
    表示("私の年齢は整数歳です改行", 年齢);
    戻る 0;
}'''
        },
        {
            "name": "繰り返し処理 (JCL)",
            "code": '''主関数() {
    整数型 i;
    繰り返し(i = 1; i <= 3; i++) {
        表示("カウント: 整数改行", i);
    }
    戻る 0;
}'''
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n【テスト {i}】{test['name']}")
        print("-" * 50)
        print("JCLコード:")
        print(test['code'])
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{base_url}/run",
                json={"code": test['code']},
                timeout=15
            )
            
            result = response.json()
            print(f"✅ レスポンス: {response.status_code}")
            print(f"🎯 成功: {result.get('ok', False)}")
            print(f"📍 ステージ: {result.get('stage', 'unknown')}")
            print(f"📤 出力:")
            print(result.get('stdout', '(なし)'))
            
            if result.get('stderr'):
                print(f"⚠️ エラー情報:")
                print(result.get('stderr'))
                
        except Exception as e:
            print(f"❌ リクエストエラー: {e}")
    
    print("\n🎉 テスト完了！")

if __name__ == "__main__":
    test_real_jcl()

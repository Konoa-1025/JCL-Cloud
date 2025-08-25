import requests
import json

def test_auth_api():
    base_url = "http://127.0.0.1:8080"  # ローカルテスト
    
    print("🔒 認証機能テスト開始")
    print("=" * 50)
    
    # 1. 認証なしでアクセス試行
    print("1. 認証なしでのアクセステスト...")
    try:
        response = requests.post(f"{base_url}/run", json={"code": "主関数() { 戻る 0; }"})
        print(f"ステータス: {response.status_code} (401が期待される)")
        if response.status_code == 401:
            print("✅ 認証なしアクセスが正しく拒否されました")
        else:
            print("❌ 認証なしでアクセスできてしまいました")
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print("\n" + "=" * 50)
    
    # 2. 正しいアカウントでログイン
    print("2. 許可されたアカウントでのログインテスト...")
    
    test_accounts = [
        {
            "email": "norifumi.kondo.it@gmail.com",
            "password": "jcl2025",
            "name": "メインアカウント"
        },
        {
            "email": "studio.delta.tester1@gmail.com", 
            "password": "jcl2025",
            "name": "テスターアカウント"
        }
    ]
    
    for account in test_accounts:
        print(f"\n{account['name']} ({account['email']}) でログイン中...")
        
        try:
            # ログイン
            login_response = requests.post(f"{base_url}/login", json={
                "email": account['email'],
                "password": account['password']
            })
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                token = login_data['access_token']
                print(f"✅ ログイン成功！トークン取得")
                
                # 認証済みでJCL実行
                run_response = requests.post(f"{base_url}/run", 
                    json={"code": "主関数() { 表示(\"認証テスト成功！改行\"); 戻る 0; }"},
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if run_response.status_code == 200:
                    result = run_response.json()
                    print(f"✅ JCL実行成功: {result.get('stdout', '').strip()}")
                else:
                    print(f"❌ JCL実行失敗: {run_response.status_code}")
                    
            else:
                print(f"❌ ログイン失敗: {login_response.status_code}")
                print(f"エラー: {login_response.text}")
                
        except Exception as e:
            print(f"❌ テストエラー: {e}")
    
    print("\n" + "=" * 50)
    
    # 3. 許可されていないアカウントでログイン試行
    print("3. 許可されていないアカウントでのログインテスト...")
    
    try:
        unauthorized_response = requests.post(f"{base_url}/login", json={
            "email": "unauthorized@example.com",
            "password": "jcl2025"
        })
        
        if unauthorized_response.status_code == 403:
            print("✅ 許可されていないアカウントが正しく拒否されました")
        else:
            print(f"❌ 許可されていないアカウントがログインできてしまいました: {unauthorized_response.status_code}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")
    
    print("\n🎉 認証テスト完了！")

if __name__ == "__main__":
    test_auth_api()

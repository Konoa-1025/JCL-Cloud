import requests
import json

def test_api():
    url = "http://127.0.0.1:8080/run"
    data = {"code": "主関数{ 表示(\"やっほー\\n\"); 戻る; }"}
    
    try:
        response = requests.post(url, json=data)
        print("ステータスコード:", response.status_code)
        print("レスポンス:", response.json())
    except Exception as e:
        print("エラー:", e)

if __name__ == "__main__":
    test_api()

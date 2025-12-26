import json
import os
import datetime
import requests

class Ledger:
    def __init__(self, filename="ledger.json"):
        self.filename = filename
        self.github_token = os.getenv("MY_GITHUB_TOKEN")
        self.gist_id = os.getenv("GIST_ID")
        # 起動時にGistから最新データを取得、失敗したらローカルを読み込む
        self.data = self.sync_from_gist()

    def sync_from_gist(self):
        """Gistからデータをダウンロードします。"""
        if self.github_token and self.gist_id:
            try:
                url = f"https://api.github.com/gists/{self.gist_id}"
                headers = {"Authorization": f"token {self.github_token}"}
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    gist_data = response.json()
                    # 指定したファイル名がGist内に存在するか確認
                    if self.filename in gist_data["files"]:
                        content = gist_data["files"][self.filename]["content"]
                        # 中身が空（新規作成直後など）の場合は空辞書を返す
                        if not content.strip():
                            return {}
                        print(f"[SYSTEM] Gistからデータを読み込みました: {self.filename}")
                        return json.loads(content)
                else:
                    print(f"[WARNING] Gistからの取得に失敗 (Status: {response.status_code})")
            except Exception as e:
                print(f"[WARNING] Gist同期エラー: {e}")
        
        return self.load_local()

    def load_local(self):
        """ローカルファイルから読み込みます。"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] ローカルファイルの読み込み失敗: {e}")
                return {}
        return {}

    def save(self):
        """データを保存し、Gistへアップロードします。"""
        # 1. まずローカルファイルを更新
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] ローカル保存失敗: {e}")

        # 2. Gistへアップロード（GitHub Actions終了後もデータを残すため）
        if self.github_token and self.gist_id:
            try:
                url = f"https://api.github.com/gists/{self.gist_id}"
                headers = {"Authorization": f"token {self.github_token}"}
                payload = {
                    "files": {
                        self.filename: {
                            "content": json.dumps(self.data, indent=4, ensure_ascii=False)
                        }
                    }
                }
                res = requests.patch(url, headers=headers, json=payload)
                if res.status_code == 200:
                    print("[SYSTEM] Gistへのバックアップが完了しました。")
                else:
                    print(f"[ERROR] Gistバックアップ失敗 (Status: {res.status_code})")
            except Exception as e:
                print(f"[ERROR] Gist通信エラー: {e}")

    def get_user(self, user_id):
        """
        ユーザーデータを取得し、新規ユーザーなら初期化します。
        """
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "xp": 0,
                "money": 100,
                "lang": "ja", # 日本語固定運用ですが、互換性のために保持
                "joined_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                "last_active": "N/A"
            }
        
        u = self.data[uid]
        # 既存データのフィールド補完
        if "money" not in u: u["money"] = 100
        if "xp" not in u: u["xp"] = 0
        return u

    def add_xp(self, user_id, amount):
        """貢献度を加算します。"""
        u = self.get_user(user_id)
        u["xp"] += amount
        u["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

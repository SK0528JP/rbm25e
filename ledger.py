import os
import json
import requests
import datetime

class Ledger:
    def __init__(self):
        self.gist_id = os.getenv("GIST_ID")
        self.github_token = os.getenv("MY_GITHUB_TOKEN")
        self.data = self._load_from_gist()

    def _load_from_gist(self):
        """Gistからデータを取得する"""
        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {"Authorization": f"token {self.github_token}"}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            content = res.json()["files"]["soviet_ledger.json"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"[ERROR] Gistロード失敗: {e}")
            return {}

    def save(self):
        """現在のデータをGistへ書き込む"""
        try:
            url = f"https://api.github.com/gists/{self.gist_id}"
            headers = {"Authorization": f"token {self.github_token}"}
            payload = {
                "files": {
                    "soviet_ledger.json": {
                        "content": json.dumps(self.data, indent=4, ensure_ascii=False)
                    }
                }
            }
            res = requests.patch(url, headers=headers, json=payload)
            res.raise_for_status()
        except Exception as e:
            print(f"[ERROR] Gist保存失敗: {e}")

    def get_user(self, user_id):
        """ユーザーデータを取得し、存在しなければ新規作成する"""
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "xp": 0,
                "money": 0,
                "last_active": "N/A",
                "joined_at": datetime.datetime.now().strftime("%Y-%m-%d")
            }
        return self.data[uid]

    def add_xp(self, user_id, amount):
        """XPを加算し、最終活動時間を更新する"""
        u = self.get_user(user_id)
        u["xp"] += amount
        u["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 頻繁なセーブを避けるため、ここではsave()を呼ばない。
        # 必要に応じて各コマンド側や、一定間隔でsave()を呼ぶ。

import requests
import json
from datetime import datetime

class Ledger:
    def __init__(self, gist_id, github_token):
        """
        Gistを利用したデータ永続化ユニット。
        """
        self.gist_id = gist_id
        self.github_token = github_token
        self.file_name = "ledger.json"
        self.data = self._load_from_gist()

    def _load_from_gist(self):
        """
        Gistから最新のJSONデータを取得します。
        """
        headers = {"Authorization": f"token {self.github_token}"}
        url = f"https://api.github.com/gists/{self.gist_id}"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            gist_data = response.json()
            
            # 指定したファイル名の内容を取得
            file_info = gist_data.get("files", {}).get(self.file_name)
            if file_info:
                content = file_info.get("content", "{}")
                return json.loads(content)
            else:
                print(f"⚠️ {self.file_name} が見つかりません。新規作成します。")
                return {}
        except Exception as e:
            print(f"❌ Load Error: {e}")
            return {}

    def save(self):
        """
        現在のデータをGistに保存（上書き）します。
        """
        headers = {"Authorization": f"token {self.github_token}"}
        url = f"https://api.github.com/gists/{self.gist_id}"
        
        payload = {
            "files": {
                self.file_name: {
                    "content": json.dumps(self.data, indent=4, ensure_ascii=False)
                }
            }
        }
        
        try:
            response = requests.patch(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"💾 Data saved to Gist at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ Save Error: {e}")

    def get_user(self, user_id):
        """
        ユーザーデータを取得します。存在しない場合は初期化します。
        """
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "money": 100,
                "xp": 0,
                "joined_at": datetime.now().strftime("%Y-%m-%d")
            }
        return self.data[uid]

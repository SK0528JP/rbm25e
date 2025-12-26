import json
import os
import datetime

class Ledger:
    def __init__(self, filename="ledger.json"):
        self.filename = filename
        self.data = self.load()

    def load(self):
        """データベースファイルを読み込みます。存在しない場合は新規作成します。"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"[ERROR] {self.filename} の読み込みに失敗しました。バックアップを確認してください。")
                return {}
        return {}

    def save(self):
        """現在のメモリ上のデータをファイルへ書き込みます。"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] データの保存中にエラーが発生しました: {e}")

    def get_user(self, user_id):
        """
        ユーザーデータを取得し、不足しているフィールドがあれば
        Rb m/25 の標準規格に基づいて補完します。
        """
        uid = str(user_id)
        
        # 新規ユーザーの初期定義
        if uid not in self.data:
            self.data[uid] = {
                "xp": 0,
                "money": 100,
                "lang": "ja",           # デフォルト言語設定
                "joined_at": datetime.datetime.now().strftime("%Y-%m-%d"),
                "last_active": "N/A"
            }
        
        # 既存ユーザーへのフィールド補完（マイグレーション）
        u = self.data[uid]
        if "lang" not in u:
            u["lang"] = "ja"
        if "money" not in u:
            u["money"] = 100
        if "xp" not in u:
            u["xp"] = 0
            
        return u

    def add_xp(self, user_id, amount):
        """貢献度(XP)を加算し、最終アクティブ時間を更新します。"""
        u = self.get_user(user_id)
        u["xp"] += amount
        # ISO形式に近いクリーンな日付表記（北欧モダン・スタイル）
        u["last_active"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

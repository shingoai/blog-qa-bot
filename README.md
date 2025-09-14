# ブログスクール Q&Aボット

ブログスクール生徒向けのAI Q&Aボットシステムです。

## 機能

- 🤖 ChatGPT風のチャットインターフェース
- 📚 教材（テキスト・動画文字起こし）のナレッジベース管理
- 🔍 教材に基づいた正確な回答生成
- 🔗 Utage URLの自動表示
- 📊 質問履歴の分析とエクスポート
- 🔐 パスワード認証

## セットアップ

### 1. 環境構築

```bash
# リポジトリをクローン
git clone [your-repo-url]
cd blog-school-qa-bot

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`を`.env`にコピーして、必要な情報を設定：

```bash
cp .env.example .env
```

`.env`ファイルを編集：
```
OPENAI_API_KEY=your_openai_api_key_here
AUTH_PASSWORD=your_system_password_here
```

### 3. ローカルで起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセス

## 使い方

### 生徒として

1. パスワードを入力してログイン
2. チャット画面で質問を入力
3. AIが教材を参照して回答

### 管理者として

1. **教材管理ページ**
   - テキスト教材の追加
   - 動画文字起こしの追加
   - Utage URLの設定

2. **質問分析ページ**
   - 質問統計の確認
   - よくある質問の分析
   - データのエクスポート

## Streamlit Cloudへのデプロイ

1. GitHubにリポジトリをプッシュ

2. [Streamlit Cloud](https://streamlit.io/cloud)にログイン

3. "New app"をクリック

4. リポジトリを選択し、以下を設定：
   - Branch: main
   - Main file path: app.py

5. "Advanced settings"で環境変数を設定：
   ```
   OPENAI_API_KEY = "your_key"
   AUTH_PASSWORD = "your_password"
   ```

6. "Deploy"をクリック

## 技術スタック

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o-mini
- **Vector DB**: ChromaDB
- **Language**: Python 3.9+

## ディレクトリ構造

```
blog-school-qa-bot/
├── app.py                 # メインアプリ
├── components/            # コンポーネント
│   ├── knowledge_base.py  # ナレッジベース管理
│   └── question_logger.py # 質問ログ管理
├── pages/                 # Streamlitページ
│   ├── 1_📚_教材管理.py
│   └── 2_📊_質問分析.py
├── utils/                 # ユーティリティ
│   └── auth.py           # 認証
├── requirements.txt       # 依存関係
└── .env                  # 環境変数（gitignore）
```

## トラブルシューティング

### ChromaDBのエラー
```bash
pip install --upgrade chromadb
```

### OpenAI APIキーエラー
`.env`ファイルのAPIキーが正しいか確認

### メモリ不足エラー
Streamlit Cloudの無料枠では1GBの制限があります。
大量の教材を追加する場合は、有料プランを検討してください。

## ライセンス

MIT
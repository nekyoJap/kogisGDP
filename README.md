# kogisGDP - 競輪AI予想システム

競輪レースの展開予想をAIで支援するシステムです。生成AIとRAG（Retrieval-Augmented Generation）を活用し、独自データと公開データを組み合わせて予想精度を向上させます。

## 🎯 主な機能

### 1. AI展開予想機能
- 生成AIのAPIと独自データを活用したRAGベースの予想
- 選手情報、過去レースデータ、独自の予想ロジックを参照
- コンテキストを考慮した根拠のある予想生成

### 2. 予想ボード機能
- インタラクティブな予想操作UI
- ドラッグ&ドロップで展開を視覚的に編集
- リアルタイムでの予想調整

### 3. シミュレーション機能
- AI予想と手動予想の統合
- レース展開のシミュレーション実行
- 結果の可視化と分析

---

## 📁 ディレクトリ構造

```
kogisGDP/
├── README.md                    # プロジェクト概要（このファイル）
├── docs/                        # ドキュメント
│   ├── architecture.md          # アーキテクチャ設計書
│   ├── api-design.md            # API設計書
│   └── data-model.md            # データモデル設計書
├── backend/                     # バックエンド（Python/FastAPI）
│   ├── api/                     # REST APIエンドポイント
│   ├── rag/                     # RAGシステム
│   ├── prediction/              # 予想ロジック
│   ├── simulation/              # シミュレーションエンジン
│   └── scraper/                 # データスクレイピング
├── frontend/                    # フロントエンド（React/TypeScript）
│   └── src/
│       ├── components/          # UIコンポーネント
│       └── pages/               # ページ
├── data/                        # データ
│   ├── raw/                     # 生データ（選手情報、過去レース等）
│   ├── processed/               # 加工済みデータ
│   └── vectors/                 # ベクトルデータ（RAG用）
└── tests/                       # テスト
```

---

## 🛠️ 技術スタック

### バックエンド
| 技術 | 用途 |
|------|------|
| Python 3.11+ | メイン言語 |
| FastAPI | REST APIフレームワーク |
| LangChain | RAG/AI連携フレームワーク |
| ChromaDB / FAISS | ベクトルデータベース |
| BeautifulSoup / Selenium | Webスクレイピング |

### 生成AI API
| サービス | 特徴 |
|----------|------|
| OpenAI GPT-4/GPT-3.5 | 高品質（有料） |
| Groq (Llama3/Mixtral) | 高速、無料枠あり |
| Google Gemini | 無料枠あり |
| Ollama | ローカル実行、完全無料 |

### フロントエンド
| 技術 | 用途 |
|------|------|
| React | UIフレームワーク |
| TypeScript | 型安全な開発 |
| Tailwind CSS | スタイリング |
| shadcn/ui | UIコンポーネント |
| Zustand | 状態管理 |

---

## 📅 開発ロードマップ

### Phase 1: 基盤構築 🔨
- [x] プロジェクト初期設定
- [x] ディレクトリ構造作成
- [ ] 開発環境セットアップ（Python/Node.js）
- [ ] 基本的なAPI構造の実装
- [ ] データモデル設計

### Phase 2: データ収集・整備 📊
- [ ] 競輪公式サイトからのスクレイピング実装
- [ ] 選手データの収集・整形
- [ ] 過去レースデータの収集・整形
- [ ] 独自予想データの入力フォーマット作成
- [ ] データベース設計・構築

### Phase 3: RAG/AI予想機能 🤖
- [ ] ベクトルDB構築（ChromaDB）
- [ ] 知識ベースの埋め込み処理
- [ ] 生成AI API連携（OpenAI/Groq）
- [ ] RAGパイプライン構築
- [ ] 予想ロジックの実装
- [ ] プロンプトエンジニアリング

### Phase 4: 予想ボード 🎮
- [ ] フロントエンド環境構築
- [ ] 予想ボードUIデザイン
- [ ] ドラッグ&ドロップ機能実装
- [ ] バックエンドAPI連携
- [ ] リアルタイム更新機能

### Phase 5: シミュレーション 🏁
- [ ] シミュレーションエンジン設計
- [ ] AI予想とボード予想の統合
- [ ] レース展開シミュレーション
- [ ] 結果可視化コンポーネント
- [ ] 統計・分析機能

### Phase 6: 最適化・リリース 🚀
- [ ] パフォーマンス最適化
- [ ] テスト整備
- [ ] ドキュメント整備
- [ ] デプロイ環境構築

---

## 🚀 クイックスタート

### 前提条件
- Python 3.11+
- Node.js 18+
- Git

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/nekyoJap/kogisGDP.git
cd kogisGDP

# バックエンドセットアップ
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# フロントエンドセットアップ
cd ../frontend
npm install
```

### 実行

```bash
# バックエンド起動
cd backend
uvicorn main:app --reload

# フロントエンド起動（別ターミナル）
cd frontend
npm run dev
```

---

## 📝 ライセンス

MIT License

---

## 👥 コントリビューション

プルリクエスト歓迎です！

---

*最終更新: 2026年1月21日*

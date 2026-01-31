# kogisGDP 開発ガイド

競輪AI予想システム（kogisGDP）の開発方針・技術ガイドライン

---

## 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| フロントエンド | React 18.x + TypeScript | 静的HTML版（docs/）も併用 |
| バックエンド | Python 3.11+ / FastAPI | スクレイピング・API |
| AI/RAG | LangChain + ChromaDB/FAISS | 予想生成 |
| スクレイピング | BeautifulSoup / Selenium | keirin.jp等 |

---

## ディレクトリ構造

```
kogisGDP/
├── docs/                    # GitHub Pages公開用（静的HTML）
│   ├── index.html          # 予想ボード（表形式）
│   ├── bank.html           # バンク版（ビジュアル）
│   ├── race-merge.html     # 出走表×選手評価マージビュー
│   └── *.js, *.css
├── data/                    # データファイル
│   ├── raw/                # 生データ
│   ├── processed/          # 加工済み
│   └── vectors/            # ベクトルDB用
├── backend/                 # バックエンド
│   ├── api/                # REST API
│   ├── scraper/            # スクレイパー
│   ├── prediction/         # 予想ロジック
│   └── rag/                # RAGシステム
└── frontend/               # React版（将来）
```

---

## アーキテクチャ方針

### レイヤー分離

```
┌─────────────────────────────────────┐
│   Presentation (React / HTML)       │  UI層
├─────────────────────────────────────┤
│   Application (Use Cases)           │  ユースケース層
├─────────────────────────────────────┤
│   Domain (Models, Services)         │  ドメイン層
├─────────────────────────────────────┤
│   Infrastructure (DB, API, Scraper) │  インフラ層
└─────────────────────────────────────┘
```

- **依存の方向**: 外側 → 内側（ドメイン層は他に依存しない）
- **ドメインロジック**: フレームワークに依存させない

### フロントエンド構造（React版）

```
src/
├── features/               # 機能単位
│   ├── race/              # レース関連
│   │   ├── components/    # UIコンポーネント
│   │   ├── hooks/         # カスタムフック
│   │   ├── api/           # API呼び出し
│   │   └── types/         # 型定義
│   └── prediction/        # 予想関連
├── shared/                 # 共通
│   ├── components/
│   └── utils/
└── app/                    # アプリ設定
```

---

## データモデル

### 出走表（Race Entry）

```typescript
interface RaceEntry {
  raceInfo: {
    date: string;           // "2025-12-30"
    venue: string;          // "平塚"
    raceNumber: number;     // 11
    raceName: string;       // "KEIRINグランプリ2025"
    grade: string;          // "GP", "GI", "GII", "GIII", "FI", "FII"
    startTime: string;      // "16:30"
  };
  entries: EntryPlayer[];
}

interface EntryPlayer {
  frameNumber: number;      // 枠番 1-6
  carNumber: number;        // 車番 1-9
  name: string;             // 選手名
  prefecture: string;       // 府県
  age: number;
  term: number;             // 期別
  rank: string;             // "SS", "S1", "S2", "A1", "A2", "A3"
  style: string;            // 脚質: "逃", "追", "両"
  score: number;            // 競走得点
  winRate: number;          // 勝率
  prediction?: string;      // 予想印: "◎", "○", "▲", "△", "×"
}
```

### 選手評価（Player Evaluation）

```typescript
interface PlayerEvaluation {
  name: string;             // 選手名（マージキー）
  rank: string;             // 級班
  prefecture: string;       // 府県
  home: string;             // ホームバンク
  term: string;             // 期別
  type1: string;            // タイプ1: "先行", "追い込み", "自在", "捲"
  type2?: string;           // タイプ2
  leadWill: string;         // 先行意欲: "◎", "◯", "△", "✕"
  banteExp: string;         // 番手経験
  speed: string;            // スピード
  attack: string;           // 仕掛け
  stamina: string;          // スタミナ
  keirinIQ: string;         // 競輪IQ
  comment?: string;         // コメント
}
```

---

## API設計方針

### エンドポイント規約

```
GET  /api/v1/races                    # レース一覧
GET  /api/v1/races/{raceId}           # レース詳細
GET  /api/v1/races/{raceId}/entries   # 出走表
POST /api/v1/predictions              # 予想生成
```

### エラーレスポンス形式

```json
{
  "error": {
    "code": "RACE_NOT_FOUND",
    "message": "指定されたレースが存在しません",
    "timestamp": "2026-01-31T10:30:00+09:00"
  }
}
```

### HTTPステータスコード

| コード | 用途 |
|-------|------|
| 200 | 成功 |
| 400 | リクエスト形式エラー |
| 404 | リソース未存在 |
| 422 | 業務ルールエラー |
| 500 | サーバーエラー |

---

## 命名規約

### ファイル・ディレクトリ

- **コンポーネント**: PascalCase（`RaceEntry.tsx`）
- **ユーティリティ**: camelCase（`formatDate.ts`）
- **スタイル**: kebab-case（`race-merge.css`）

### 変数・関数

- **変数**: camelCase（`raceData`, `playerList`）
- **定数**: UPPER_SNAKE_CASE（`MAX_PLAYERS`）
- **型/インターフェース**: PascalCase（`RaceEntry`, `PlayerEvaluation`）

### 日本語対応

- ユビキタス言語として日本語の概念を尊重
- コード内は英語、UIは日本語

---

## 競輪ドメイン知識

### 車番カラー

| 車番 | 色 |
|-----|-----|
| 1 | 白 |
| 2 | 黒 |
| 3 | 赤 |
| 4 | 青 |
| 5 | 黄 |
| 6 | 緑 |
| 7 | 橙 |
| 8 | 桃 |
| 9 | 紫 |

### 級班

| 級班 | 説明 |
|-----|------|
| SS | S級S班（トップ9名） |
| S1 | S級1班 |
| S2 | S級2班 |
| A1 | A級1班 |
| A2 | A級2班 |
| A3 | A級3班 |

### 脚質

| 脚質 | 説明 |
|-----|------|
| 逃 | 先行（逃げ） |
| 追 | 追い込み |
| 両 | 自在（両方可能） |

### グレード

| グレード | 説明 |
|---------|------|
| GP | グランプリ |
| GI | G1 |
| GII | G2 |
| GIII | G3 |
| FI | F1 |
| FII | F2 |

---

## 開発フロー

1. **ブランチ**: `feature/{機能名}` で作業
2. **コミット**: 日本語でも可、意図が明確なメッセージ
3. **テスト**: 主要ロジックはテストを書く
4. **PR**: mainへのマージはPR経由

---

## 参考リンク

- [keirin.jp](https://keirin.jp/) - 公式出走表
- [KEIRIN.kdreams.jp](https://keirin.kdreams.jp/) - 楽天Kドリームス

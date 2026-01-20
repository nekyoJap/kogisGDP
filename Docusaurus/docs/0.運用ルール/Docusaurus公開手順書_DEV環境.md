# Docusaurus公開手順書（DEV環境）

> **前提:** ZIPファイル作成、S3アップロード、CodeBuild Plan確認は完了済み

---

## 1. 概要

### 1.1 この手順書で行うこと

Docusaurus（ドキュメントサイト）をDEV環境のCloudFront経由で公開します。

```
┌────────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Backlog Git   │────▶│  CodeBuild  │────▶│  S3 + CloudFront│
│  (ソースコード)│     │  (ビルド)   │     │  (公開)         │
└────────────────┘     └─────────────┘     └─────────────────┘
```

### 1.2 関連リソース

| リソース | DEV環境の値 |
|---------|------------|
| AWSアカウントID | `696505809298` |
| S3（コンテンツ） | `hcredit-dev-web-content-696505809298` |
| S3（ソース） | `hcredit-dev-source-696505809298` |
| CloudFront | apply後に確認 |

### 1.3 関連リポジトリ

| リポジトリ | 用途 | パス |
|-----------|------|------|
| `dev_pfm_housecreditcard.git` | Docusaurusソース | `Docusaurus/` |
| `infrastructure.git` | インフラ定義（Terraform） | `iac-terraform/` |

---

## 2. インフラ構築手順（apply実行）

### 2.1 構築順序

以下の順番でCodeBuildを実行します。**順番を守ってください。**

| 順番 | TARGET_DIR | 説明 |
|------|------------|------|
| 1 | `live/dev/app-web/s3-web` | Docusaurusコンテンツ格納用S3 |
| 2 | `live/dev/edge/waf` | IPアクセス制限（WAF） |
| 3 | `live/dev/edge/lambda-edge` | 認証処理 |
| 4 | `live/dev/edge/cloudfront` | CDN配信 |
| 5 | `live/dev/cicd/codebuild-docusaurus` | Docusaurusビルド用CodeBuild |

### 2.2 CodeBuild実行手順（AWSコンソール）

#### Step 1: AWSマネジメントコンソールにログイン

1. ブラウザで https://aws.amazon.com/console/ を開く
2. DEV環境のアカウント（`696505809298`）にログイン

#### Step 2: CodeBuildを開く

1. 検索バーに `CodeBuild` と入力
2. **CodeBuild** をクリック
3. リージョンが **ap-northeast-1（東京）** であることを確認

#### Step 3: ビルドプロジェクトを選択

1. 左メニューから **ビルドプロジェクト** をクリック
2. `hcredit-dev-build-iac` をクリック

#### Step 4: 環境変数を設定してビルド開始

1. **ビルドを開始** → **環境変数のオーバーライドでビルドを開始** をクリック
2. 以下の環境変数を設定：

| 名前 | 値 | 種類 |
|------|-----|------|
| `COMMAND` | `apply` | プレーンテキスト |
| `TARGET_DIR` | `live/dev/app-web/s3-web` | プレーンテキスト |

3. **ビルドを開始** をクリック

#### Step 5: ビルド完了を待つ

- **緑色のチェック**（成功）が表示されるまで待機
- エラーの場合は **ビルドログ** を確認

#### Step 6: 次のリソースを構築

- 2.1の順番通りに、`TARGET_DIR` を変更して繰り返す

---

## 3. CloudFront URL確認

### 3.1 CloudFrontドメイン名の取得

1. AWSコンソールで **CloudFront** を開く
2. ディストリビューション一覧から `hcredit-dev-cdn` を探す
3. **ドメイン名** 列の値をコピー（例: `d1234567890abc.cloudfront.net`）

### 3.2 アクセス確認

ブラウザで以下のURLにアクセス：

```
https://d1234567890abc.cloudfront.net/docs/
```

> **注意:** IPアクセス制限がかかっているため、許可されたIPからのみアクセス可能

---

## 4. Docusaurusデプロイ手順

### 4.1 自動デプロイ（推奨）

Docusaurusのソースコードを更新してGit pushすると自動的にデプロイされます。

#### Step 1: ドキュメントを編集

```
dev_pfm_housecreditcard/
└── Docusaurus/
    └── docs/
        └── 2.システム全体方針/    ← ここにMarkdownファイルを追加・編集
```

#### Step 2: Git push

```bash
cd c:\Users\10105790\dev_pfm_housecreditcard
git add -A
git commit -m "docs: ドキュメント追加"
git push origin main
```

#### Step 3: CodeBuildが自動実行

1. AWSコンソールで **CodeBuild** を開く
2. `hcredit-dev-build-docusaurus` のビルド状況を確認

#### Step 4: 公開を確認

- CloudFrontのURL（`/docs/`）にアクセスして確認
- キャッシュが残っている場合は5分程度待つ

### 4.2 手動デプロイ（緊急時）

#### Step 1: ソースZIP作成

```bash
cd c:\Users\10105790\dev_pfm_housecreditcard
git archive --format=zip HEAD -o source.zip
```

#### Step 2: S3にアップロード

```bash
aws s3 cp source.zip s3://hcredit-dev-source-696505809298/docusaurus/source.zip
```

#### Step 3: CodeBuildを手動実行

1. AWSコンソールで **CodeBuild** → `hcredit-dev-build-docusaurus` を開く
2. **ビルドを開始** をクリック

---

## 5. パスルーティング構成

CloudFrontは以下のパスでルーティングします：

| パス | 転送先 | 用途 |
|-----|--------|------|
| `/` | S3 | Welcomeページ |
| `/docs/*` | S3 | **Docusaurus** |
| `/web/*` | ALB | Webアプリケーション |
| `/api/*` | ALB | API |
| `/dodoai/*` | ALB | DoDoAI |

---

## 6. トラブルシューティング

### 6.1 よくあるエラーと対処法

| 症状 | 原因 | 対処法 |
|------|------|--------|
| CodeBuild失敗: `AccessDenied` | IAM権限不足 | 前のリソースがapply済みか確認 |
| CloudFront 403 Forbidden | IPアクセス制限 | 許可IPか確認（WAF設定） |
| 更新が反映されない | CloudFrontキャッシュ | 5分待つ or 手動Invalidation |
| `/docs/` で404 | S3にファイルがない | CodeBuildログを確認 |

### 6.2 ログの確認方法

#### CodeBuildログ

1. AWSコンソールで **CodeBuild** を開く
2. 対象ビルドプロジェクトをクリック
3. 失敗したビルドの **ビルドログ** をクリック

#### CloudFrontアクセスログ（有効な場合）

1. S3バケットのログを確認

---

## 7. 構成図（PlantUML）

詳細な構成図は以下のファイルを参照：

- `Docusaurus/docs/0.運用ルール/architecture-cloudfront.puml`

VS Codeの PlantUML 拡張機能で `Alt+D` を押すとプレビューできます。

---

## 8. 参考リンク

- [Docusaurus公式ドキュメント](https://docusaurus.io/docs)
- [AWS CodeBuild ユーザーガイド](https://docs.aws.amazon.com/codebuild/)
- [Terragrunt ドキュメント](https://terragrunt.gruntwork.io/docs/)

---

## 更新履歴

| 日付 | 内容 | 担当 |
|------|------|------|
| 2026/01/20 | 初版作成 | - |

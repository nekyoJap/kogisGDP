# Docusaurus 仕様書ドキュメント

このプロジェクトは、Docusaurusを使用した仕様書ドキュメントサイトです。

## 前提条件

- Node.js 18.0以上
- npm または yarn
- AWS アカウント（デプロイ時）

## セットアップ手順

### 1. 依存関係のインストール

```bash
npm install
```

または

```bash
yarn install
```

### 2. 開発サーバーの起動

```bash
npm start
```

または

```bash
yarn start
```

ブラウザで `http://localhost:3000` が自動的に開きます。

### 3. ビルド

本番用の静的ファイルを生成します。

```bash
npm run build
```

または

```bash
yarn build
```

ビルドされたファイルは `build` ディレクトリに出力されます。

## デプロイ方法

このプロジェクトは、GitHub ActionsとAWS CodeBuildの両方に対応しています。

---

## デプロイ方法1: GitHub Actions（推奨）

GitHubリポジトリにプッシュすると自動的にビルド・デプロイされます。

### セットアップ手順

#### 1. GitHubリポジトリのSecrets設定

GitHubリポジトリの Settings → Secrets and variables → Actions で以下を設定：

| Secret名 | 説明 | 必須 |
|---------|------|------|
| `AWS_ACCESS_KEY_ID` | AWSアクセスキーID | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWSシークレットアクセスキー | ✅ |
| `AWS_REGION` | AWSリージョン（例: `ap-northeast-1`） | ✅ |
| `S3_BUCKET_NAME` | デプロイ先のS3バケット名 | ✅ |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront Distribution ID | ❌ オプション |

#### 2. IAMユーザー権限

以下の権限を持つIAMユーザーを作成：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 3. デプロイ実行

```bash
git add .
git commit -m "Update documentation"
git push origin main
```

GitHub Actionsが自動的に実行されます。進捗は「Actions」タブで確認できます。

---

## デプロイ方法2: AWS CodeBuild

AWS環境内で完結するCI/CDパイプラインを構築します。

### セットアップ手順

#### 1. S3バケットの作成

```bash
# AWS CLIでバケット作成
aws s3 mb s3://your-docusaurus-bucket --region ap-northeast-1

# 静的ウェブサイトホスティング有効化
aws s3 website s3://your-docusaurus-bucket \
  --index-document index.html \
  --error-document index.html
```

#### 2. S3バケットポリシー設定

バケットを公開するためのポリシー：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-docusaurus-bucket/*"
    }
  ]
}
```

#### 3. CodeBuildプロジェクト作成

1. AWS Management Consoleで CodeBuild を開く
2. 「ビルドプロジェクトの作成」をクリック
3. 以下を設定：

**プロジェクト設定:**
- プロジェクト名: `docusaurus-build`

**ソース:**
- ソースプロバイダ: GitHub または AWS CodeCommit
- リポジトリ: このプロジェクトのリポジトリを選択
- Webhook: 有効化（自動ビルド用）
  - イベントタイプ: PUSH

**環境:**
- 環境イメージ: マネージド型イメージ
- オペレーティングシステム: Ubuntu
- ランタイム: Standard
- イメージ: aws/codebuild/standard:7.0
- 特権付与: 不要

**Buildspec:**
- ビルド仕様: buildspecファイルを使用
- Buildspecの名前: `buildspec.yml`（デフォルト）

**アーティファクト:**
- タイプ: S3
- バケット名: `your-docusaurus-bucket`
- パス: 空（ルート）

#### 4. IAMロール権限

CodeBuildが自動作成するサービスロールに以下のポリシーを追加：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-docusaurus-bucket",
        "arn:aws:s3:::your-docusaurus-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 5. 環境変数の設定

CodeBuildプロジェクトの「環境変数」セクションで設定：

| 名前 | 値 | タイプ |
|------|-----|-------|
| `S3_BUCKET_NAME` | your-docusaurus-bucket | プレーンテキスト |
| `CLOUDFRONT_DISTRIBUTION_ID` | (オプション) | プレーンテキスト |

または、Systems Manager Parameter Storeを使用（推奨）：

```bash
# パラメータ作成
aws ssm put-parameter \
  --name /docusaurus/s3-bucket-name \
  --value your-docusaurus-bucket \
  --type String

aws ssm put-parameter \
  --name /docusaurus/cloudfront-id \
  --value YOUR_DISTRIBUTION_ID \
  --type String
```

`buildspec.yml`を編集してパラメータストアから取得：

```yaml
env:
  parameter-store:
    S3_BUCKET_NAME: /docusaurus/s3-bucket-name
    CLOUDFRONT_DISTRIBUTION_ID: /docusaurus/cloudfront-id
```

#### 6. デプロイ実行

```bash
git add .
git commit -m "Update documentation"
git push origin main
```

CodeBuildが自動的にトリガーされ、ビルド・デプロイが実行されます。

---

## CloudFront設定（オプション・推奨）

グローバルに高速配信するにはCloudFrontを使用します。

### 1. CloudFront Distributionの作成

```bash
# AWS CLIで作成（またはManagement Consoleから）
aws cloudfront create-distribution \
  --origin-domain-name your-docusaurus-bucket.s3-website-ap-northeast-1.amazonaws.com \
  --default-root-object index.html
```

### 2. エラーページ設定

Docusaurusはクライアントサイドルーティングを使用するため、404エラーも`index.html`を返すように設定：

Management Console → CloudFront → Distributions → エラーページ:
- HTTPエラーコード: 403, 404
- レスポンスページパス: `/index.html`
- HTTPレスポンスコード: 200

### 3. Distribution IDを環境変数に設定

GitHub SecretsまたはCodeBuildの環境変数に`CLOUDFRONT_DISTRIBUTION_ID`を追加。

---

## プロジェクト構造

```
Docusaurus/
├── .github/
│   └── workflows/
│       └── deploy-s3.yml      # GitHub Actions設定
├── buildspec.yml              # AWS CodeBuild設定
├── .env.example               # 環境変数テンプレート
├── docs/                      # ドキュメントファイル（Markdown）
│   ├── intro.md              # トップページ
│   ├── specifications/       # 仕様書
│   └── api/                  # API仕様
├── src/
│   └── css/
│       └── custom.css        # カスタムスタイル
├── static/                   # 静的ファイル（画像など）
├── docusaurus.config.ts      # Docusaurus設定
├── sidebars.ts               # サイドバー設定
├── package.json              # 依存関係
└── tsconfig.json             # TypeScript設定
```

## ドキュメントの追加方法

1. `docs` ディレクトリ内に新しいMarkdownファイルを作成
2. ファイルの先頭にメタデータを追加：

```markdown
---
sidebar_position: 1
---

# ドキュメントタイトル

内容をここに記載...
```

3. `sidebars.ts` を編集してサイドバーに追加（必要に応じて）
4. Git にコミット・プッシュすると自動デプロイされます

## カスタマイズ

- **サイトタイトル・設定**: `docusaurus.config.ts` を編集
- **スタイル**: `src/css/custom.css` を編集
- **サイドバー構成**: `sidebars.ts` を編集

## トラブルシューティング

### GitHub Actionsがエラーになる

- Secretsが正しく設定されているか確認
- IAMユーザーの権限を確認
- S3バケット名が正しいか確認

### CodeBuildがエラーになる

- IAMロールの権限を確認
- 環境変数が正しく設定されているか確認
- CloudWatch Logsでエラーログを確認

### S3にデプロイしたがページが表示されない

- S3バケットの静的ウェブサイトホスティングが有効か確認
- バケットポリシーで公開設定されているか確認
- CloudFront使用時は、エラーページ設定（404→index.html）を確認

## 参考リンク

- [Docusaurus公式サイト](https://docusaurus.io/)
- [Markdown記法ガイド](https://docusaurus.io/docs/markdown-features)
- [AWS S3静的ウェブサイトホスティング](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [AWS CodeBuild](https://docs.aws.amazon.com/codebuild/)
- [GitHub Actions](https://docs.github.com/actions)
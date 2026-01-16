# AWS CodeBuild + S3 デプロイガイド（Docusaurus）

## 概要

このガイドでは、Docusaurusで生成した静的サイトをAWS CodeBuild経由でS3 + CloudFrontにデプロイする方法を説明します。

## 環境情報

| 項目 | 値 |
|------|-----|
| プロジェクト名 | hcredit |
| 環境 | poc |
| AWSアカウントID | 703697785925 |
| リージョン | ap-northeast-1 |
| S3バケット（コンテンツ） | `hcredit-poc-web-content-703697785925` |
| S3バケット（ソース） | `hcredit-poc-source-703697785925` |
| CodeBuildプロジェクト | `hcredit-poc-build-web` |

## アーキテクチャ

```
┌──────────────┐     ┌───────────────┐     ┌─────────────┐     ┌────────────────┐
│  Backlog Git │────▶│  S3 Source    │────▶│  CodeBuild  │────▶│ S3 Web Content │
│  (Push)      │     │  (source.zip) │     │  (Build)    │     │ (Static Site)  │
└──────────────┘     └───────────────┘     └─────────────┘     └────────────────┘
                                                                       │
                                                                       ▼
                                                               ┌────────────────┐
                                                               │  CloudFront    │
                                                               │  (CDN + WAF)   │
                                                               └────────────────┘
                                                                       │
                                                                       ▼
                                                               ┌────────────────┐
                                                               │   End Users    │
                                                               │ (IP制限あり)   │
                                                               └────────────────┘
```

---

## IaCリポジトリ構成

```
infrastructure.git
├── iac-terraform/
│   ├── live/poc/
│   │   ├── app-web/
│   │   │   └── s3-web/         # 静的コンテンツ用S3バケット
│   │   ├── cicd/
│   │   │   ├── codebuild-web/  # Webビルド用CodeBuild
│   │   │   └── s3-source/      # ソースコード用S3バケット
│   │   └── edge/
│   │       └── cloudfront/     # CloudFrontディストリビューション
│   └── modules/
│       ├── codebuild/
│       └── cloudfront/
```

---

## 1. デプロイ方法

### 方法1: 手動デプロイ（ローカルから直接）

開発・テスト時に推奨。

```bash
# 1. Docusaurusをビルド
cd Docusaurus
npm install
npm run build

# 2. S3にアップロード
aws s3 sync build/ s3://hcredit-poc-web-content-703697785925 \
  --delete \
  --profile tmn_hcredit_poc

# 3. CloudFrontキャッシュをクリア（Distribution IDを確認後）
aws cloudfront create-invalidation \
  --distribution-id <CLOUDFRONT_DISTRIBUTION_ID> \
  --paths "/*" \
  --profile tmn_hcredit_poc
```

### 方法2: CodeBuild経由デプロイ（推奨）

CI/CD パイプラインを使用した自動デプロイ。

#### Step 1: ソースコードをS3にアップロード

```bash
# リポジトリをzip化してS3にアップロード
cd dev_pfm_housecreditcard
git archive --format=zip HEAD -o source.zip

aws s3 cp source.zip s3://hcredit-poc-source-703697785925/web/source.zip \
  --profile tmn_hcredit_poc
```

#### Step 2: CodeBuildを実行

```bash
# CodeBuildプロジェクトを起動
aws codebuild start-build \
  --project-name hcredit-poc-build-web \
  --profile tmn_hcredit_poc \
  --environment-variables-override \
    name=S3_BUCKET_NAME,value=hcredit-poc-web-content-703697785925,type=PLAINTEXT
```

---

## 2. IaC設定の追加

### Docusaurusデプロイ用のCodeBuild権限追加

現在のCodeBuildモジュールに、S3（web-content）へのデプロイ権限とCloudFrontキャッシュ無効化権限を追加する必要があります。

#### `iac-terraform/modules/codebuild/main.tf` に追加

```hcl
# S3 web content bucket への書き込み権限（Docusaurusデプロイ用）
resource "aws_iam_role_policy" "codebuild_s3_web_deploy_policy" {
  count = var.enable_s3_deploy ? 1 : 0
  name  = "${var.project_name}-${var.environment}-codebuild-s3-web-deploy-${var.app_name}"
  role  = aws_iam_role.codebuild_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          var.web_bucket_arn,
          "${var.web_bucket_arn}/*"
        ]
      }
    ]
  })
}

# CloudFront キャッシュ無効化権限
resource "aws_iam_role_policy" "codebuild_cloudfront_policy" {
  count = var.enable_cloudfront_invalidation ? 1 : 0
  name  = "${var.project_name}-${var.environment}-codebuild-cloudfront-${var.app_name}"
  role  = aws_iam_role.codebuild_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation",
          "cloudfront:GetInvalidation",
          "cloudfront:ListInvalidations"
        ]
        Resource = var.cloudfront_distribution_arn
      }
    ]
  })
}
```

#### `iac-terraform/modules/codebuild/variables.tf` に追加

```hcl
variable "enable_s3_deploy" {
  description = "Enable S3 web content deployment permissions"
  type        = bool
  default     = false
}

variable "web_bucket_arn" {
  description = "ARN of the S3 bucket for web content deployment"
  type        = string
  default     = ""
}

variable "enable_cloudfront_invalidation" {
  description = "Enable CloudFront cache invalidation permissions"
  type        = bool
  default     = false
}

variable "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  type        = string
  default     = ""
}
```

#### `iac-terraform/live/poc/cicd/codebuild-web/terragrunt.hcl` を更新

```hcl
dependency "s3_web" {
  config_path = "../../app-web/s3-web"

  mock_outputs = {
    s3_bucket_arn = "arn:aws:s3:::mock-web-bucket"
  }
}

dependency "cloudfront" {
  config_path = "../../edge/cloudfront"

  mock_outputs = {
    cloudfront_distribution_arn = "arn:aws:cloudfront::123456789012:distribution/EXAMPLE"
  }
}

inputs = {
  # ... 既存の設定 ...

  # Docusaurusデプロイ用の追加設定
  enable_s3_deploy              = true
  web_bucket_arn                = dependency.s3_web.outputs.s3_bucket_arn
  enable_cloudfront_invalidation = true
  cloudfront_distribution_arn   = dependency.cloudfront.outputs.cloudfront_distribution_arn

  # 環境変数に追加
  environment_variables = {
    RUNTIME                    = "nodejs"
    S3_BUCKET_NAME            = "${local.project_name}-${local.environment}-web-content-${local.aws_account_id}"
    CLOUDFRONT_DISTRIBUTION_ID = dependency.cloudfront.outputs.cloudfront_distribution_id
  }
}
```

---

## 3. CloudFront設定

### 現在の構成

IaCの`cloudfront`モジュールでは、以下のオリジンが設定されています：

| オリジン | パスパターン | 用途 |
|---------|------------|------|
| s3_static | デフォルト（`/*`） | Docusaurus静的サイト |
| web_alb | `/web/*` | Webアプリケーション（ECS） |
| api_alb | `/api/*` | APIアプリケーション（ECS） |

### アクセス制御

- **WAF**: IPアドレス制限（`common.hcl`の`allowed_ip_addresses`で定義）
- **OAC**: S3へのアクセスはCloudFront経由のみ許可

---

## 4. ローカル開発

### 開発サーバー起動

```bash
cd Docusaurus
npm install
npm run start
```

ブラウザで `http://localhost:3000` にアクセス。

### ビルド確認

```bash
npm run build
npm run serve  # ビルド結果をローカルで確認
```

---

## 5. トラブルシューティング

### よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| ビルド失敗: `npm ci` エラー | `package-lock.json`が古い | `npm install`で更新後コミット |
| S3アップロード失敗 | IAM権限不足 | CodeBuildロールに`s3:PutObject`権限を追加 |
| CloudFront 403エラー | OAC設定ミス | バケットポリシーを確認 |
| キャッシュが更新されない | CloudFront キャッシュ | Invalidation を実行 |

### ログ確認

```bash
# CodeBuildログ（AWSコンソールまたはCLI）
aws logs tail /aws/codebuild/hcredit-poc-web \
  --follow \
  --profile tmn_hcredit_poc
```

---

## 6. docusaurus.config.ts の本番設定

環境が構築されたら、`docusaurus.config.ts`のURLを更新してください：

```typescript
const config: Config = {
  // CloudFrontのドメインに更新
  url: 'https://xxxxxxxxxxxxxx.cloudfront.net',
  baseUrl: '/',
  
  // その他の設定...
};
```

---

## 7. 自動デプロイ設定（Webhook連携）

Backlog Gitへのpush時に自動的にビルド・デプロイを行う設定です。

### アーキテクチャ（自動デプロイ）

```
┌──────────────┐     ┌───────────────┐     ┌─────────────┐     ┌───────────────┐
│  Backlog Git │────▶│ API Gateway   │────▶│   Lambda    │────▶│ S3 (source)   │
│  (Webhook)   │     │ (POST)        │     │ (Git clone) │     │ (source.zip)  │
└──────────────┘     └───────────────┘     └─────────────┘     └───────────────┘
                                                                       │
                                                                       ▼
                                                               ┌───────────────┐
                                                               │  CodeBuild    │
                                                               │  (Build)      │
                                                               └───────────────┘
                                                                       │
                                                                       ▼
                                                               ┌───────────────┐
                                                               │ S3 + CF       │
                                                               │ (Hosting)     │
                                                               └───────────────┘
```

### 追加リソース（IaC）

| リソース | 名前 | 用途 |
|---------|------|------|
| API Gateway | hcredit-poc-webhook-api | Webhook受信エンドポイント |
| Lambda | hcredit-poc-backlog-webhook | Git clone → S3アップロード |
| SSM Parameter | /hcredit/poc/backlog-git-user | Backlog Git認証ユーザー |
| SSM Parameter | /hcredit/poc/backlog-git-password | Backlog Git認証パスワード |

### デプロイ手順

#### Step 1: Lambda関数のZIP作成

```bash
cd infrastructure/iac-terraform/lambda/backlog-webhook-handler
zip -r ../../../live/poc/cicd/webhook/lambda.zip .
```

#### Step 2: Terragrunt適用

```bash
cd infrastructure/iac-terraform/live/poc/cicd/webhook
terragrunt apply
```

#### Step 3: SSMパラメータの更新

```bash
# Backlog Git認証情報を設定
aws ssm put-parameter \
  --name "/hcredit/poc/backlog-git-user" \
  --value "your-backlog-username" \
  --type "SecureString" \
  --overwrite \
  --profile tmn_hcredit_poc

aws ssm put-parameter \
  --name "/hcredit/poc/backlog-git-password" \
  --value "your-backlog-api-key" \
  --type "SecureString" \
  --overwrite \
  --profile tmn_hcredit_poc
```

#### Step 4: Backlog Webhookの設定

1. Backlogプロジェクト設定を開く
2. **インテグレーション** → **Webhook** を選択
3. **Webhookを追加** をクリック
4. 以下を設定：

| 項目 | 値 |
|------|-----|
| 名前 | Docusaurus自動デプロイ |
| WebHook URL | `https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/poc/webhook` |
| イベント | Git Push のみチェック |

> **Note**: Webhook URLはTerragrunt適用後に出力される `api_gateway_url` の値を使用

#### Step 5: 動作確認

```bash
# テストpush
git add .
git commit -m "test: webhook trigger"
git push origin main
```

CloudWatch Logsで確認：
```bash
# Lambda関数ログ
aws logs tail /aws/lambda/hcredit-poc-backlog-webhook --follow --profile tmn_hcredit_poc

# CodeBuildログ
aws logs tail /aws/codebuild/hcredit-poc-web --follow --profile tmn_hcredit_poc
```

---

## 8. トラブルシューティング（Webhook）

| 問題 | 原因 | 解決策 |
|------|------|--------|
| Webhook受信されない | URLが間違っている | API Gateway URLを確認 |
| Lambda実行エラー | 認証情報エラー | SSMパラメータの値を確認 |
| Git clone失敗 | ネットワークエラー | Lambda がインターネットアクセス可能か確認 |
| CodeBuild未起動 | IAM権限不足 | Lambda IAMロールの権限を確認 |

### Backlog Webhook ペイロード例

```json
{
  "type": 1,
  "content": {
    "ref": "refs/heads/main",
    "revision_type": "commit",
    "revisions": [...]
  },
  "project": {...},
  "created": "2024-01-01T00:00:00Z"
}
```

---

## 参考リンク

- [Docusaurus公式ドキュメント](https://docusaurus.io/docs)
- [AWS CodeBuild ユーザーガイド](https://docs.aws.amazon.com/codebuild/)
- [Terragrunt ドキュメント](https://terragrunt.gruntwork.io/docs/)
- [Backlog Webhook ドキュメント](https://developer.nulab.com/ja/docs/backlog/api/2/get-webhook/)

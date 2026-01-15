---
id: AGPZZZZ001
title: APIガバナンス方針書
sidebar_position: 1
---

# APIガバナンス方針書

| 項目 | 内容 |
|------|------|
| ドキュメントID | AGPZZZZ001 |
| 版数 | 1.1 |
| 作成日 | 2026-01-14 |
| 最終更新日 | 2026-01-15 |
| ステータス | ドラフト |

---

## 第1章 適用範囲

### 1.1 目的

本書は、ハウスクレジット基幹システムにおける全API（同期API／非同期API／イベントAPI／バッチAPI／BFF／Process API／External Public API／ファイル連携API）の設計・運用・保守・廃止に関する共通ルールおよび判断基準を定義し、境界づけられたコンテキスト（BC）単位の自律性と、システム全体の整合性の両立を図ることを目的とする。

### 1.2 適用範囲

本書は「システム全体方針検討」に属するアーキテクチャ指針であり、コンテキストマップ／ドメインスコープ定義書／構成・運用方針書をインプットとして作成される。

本書はAPI仕様そのものではなく、「APIをどのように設計・管理・公開するか」のメタルールを定める。個々のAPI仕様（OpenAPI／AsyncAPI／Batch仕様など）は、本書の方針に従って別途作成・管理しなければならない。

**表1 — 適用範囲**

| 項目 | 記述内容 |
|------|----------|
| 対象システム | ハウスクレジット基幹システム |
| 対象BC | ドメインスコープ定義書およびコンテキストマップに定義された全BC |
| 除外対象 | 未確定（PoC／一時検証APIは例外承認対象とする想定だが詳細運用ルールは未確定） |

### 1.3 技術スタック

本システムにおける技術スタックは以下の通りとする。

**表2 — 技術スタック**

| レイヤー | 技術 | バージョン | 備考 |
|---------|------|----------|------|
| バックエンド言語 | Java | 17以上（LTS） | OpenJDK推奨 |
| バックエンドフレームワーク | Spring Boot | 3.x | Spring Framework 6.x |
| フロントエンドフレームワーク | React | 18.x以上 | TypeScript必須 |
| 同期API仕様形式 | OpenAPI | 3.0 | YAML形式で管理 |
| 非同期API仕様形式 | AsyncAPI | 2.0 | イベント定義に使用 |
| APIドキュメント生成 | Springdoc OpenAPI | - | OpenAPI仕様からSwagger UI生成 |

### 1.4 関連文書

**表3 — 関連文書一覧**

| 関連ドキュメント | 関係性 |
|------------------|--------|
| ソフトウェアアーキテクチャ方針書 | DDD/クリーンアーキテクチャの基本方針を参照する |
| コンテキストマップ | BC構造・BC間関係の定義をインプットとする |
| ドメインスコープ定義書 | BC境界の定義をインプットとする |
| 構成・運用方針書 | インフラ・運用要件と整合する |
| セキュリティ方針書 | セキュリティ要件と整合する |
| 認証・認可方針書 | 認証・認可方式と整合する |
| 非同期連携方針書 | イベント駆動連携の詳細を参照する |
| トランザクション方針書 | トランザクション制御方針を参照する |
| 例外処理ポリシー | APIエラーハンドリング方針を参照する |
| アプリケーションログ方針書 | ログ出力・監査要件を参照する |

---

## 第2章 引用規格

本書は以下の規格・標準を参照する：

- OpenAPI Specification 3.0
- AsyncAPI Specification 2.0
- RFC 7231 HTTP/1.1 Semantics and Content
- RFC 6749 OAuth 2.0 Authorization Framework
- RFC 2119 Key words for use in RFCs to Indicate Requirement Levels

---

## 第3章 用語及び定義

### 3.1 規範用語の定義

本書で使用する規範用語は RFC 2119 に準拠し、以下の意味で使用する。

**表4 — 規範用語定義**

| 用語 | 意味 |
|------|------|
| しなければならない（MUST） | この要件は絶対的に必須である。例外は認められない |
| してはならない（MUST NOT） | この行為は絶対的に禁止される。例外は認められない |
| すべきである（SHOULD） | 特別な理由がない限り、この要件に従うことが強く推奨される |
| すべきではない（SHOULD NOT） | 特別な理由がない限り、この行為を避けることが強く推奨される |
| してもよい（MAY） | この要件は任意であり、状況に応じて判断してよい |

### 3.2 ドメイン用語の定義

本書で使用する主要な用語を以下に定義する。

**表5 — 用語定義**

| 用語 | 定義 |
|------|------|
| Domain API | 単一BC内部で完結する操作を提供するAPI |
| Process API | BC横断の業務フロー・オーケストレーションを担うAPI |
| BFF | Backend for Frontend。UI最適化・プレゼンテーション層専用のAPI |
| External Public API | 外部システム・パートナー向けに公開されるAPI |
| Event API | 状態変化をイベントとして通知するAPI（Pub-Sub） |
| Batch API | 定期実行・ファイル連携などバッチ処理用のAPI |
| ACL | Anti-Corruption Layer。外部との連携時に自BCモデルを保護する翻訳層 |
| 冪等性（Idempotency） | 同じ操作を複数回実行しても、結果が1回実行した場合と同じになる性質 |
| 冪等キー | 重複リクエストを検出するための一意識別子（Idempotency-Key） |

---

## 第4章 対象BC一覧

対象BCの詳細は未確定である。確定後は、ドメインスコープ定義書およびコンテキストマップで定義されたBC一覧を参照すること。

**注記：** 対象BC一覧は、コンテキストマップおよびドメインスコープ定義書の策定完了後に確定する。

**表6 — 対象BC一覧（テンプレート）**

| BC名 | 種別 | 概要 | 備考 |
|------|------|------|------|
| （確定後に記入） | Core/Supporting/Generic | （確定後に記入） | （確定後に記入） |

---

## 第5章 APIの定義と分類

### 5.1 APIの定義

本書における「API」とは、次のすべてを含む広義のインタフェースと定義する。

- システム間・BC間の機能・データを**契約（Contract）**として公開し、連携するためのインタフェース全般
- HTTP/REST API、RPC、GraphQL、メッセージング／イベント配信（Kafka等）、バッチ連携、ファイル連携（CSV／XML／固定長など）、SFTP連携等を含む

### 5.2 API種別とガバナンス対象

**表7 — API種別とガバナンス対象**

| API種別 | 含まれる対象例 | ガバナンス上の扱い |
|---------|----------------|-------------------|
| Domain API | 売上確定BC（例）の確定・取消操作、請求BC（例）の請求締め操作 等 | 集約単位・ユースケース単位で契約を定義し、仕様レビュー対象としなければならない |
| Process API | 売上確定→請求生成フロー（例）、審査承認→発行フロー（例）などBC横断処理 | 複数BCや外部APIのオーケストレーション・例外処理・統合フロー管理を担う |
| BFF | Web/アプリ向け会員請求照会API（例）、ポイント照会画面用API（例） 等 | UI最適化・プレゼンテーション層専用。ビジネスロジックを含んではならない |
| External Public API | 銀行口座振替APIとの連携I/F（例）、外部信用情報機関照会I/F（例）、加盟店向け売上照会API（例） 等 | セキュリティ／SLA／公開レベル（Public/Partner/Internal）の管理対象とする |
| Event API | 売上確定イベント（例）、請求確定イベント（例）、入金結果イベント（例） 等 | イベントスキーマ定義・発生契機・Pub-Sub契約の管理対象とする |
| Batch API / File連携 | 会計連携用バッチIF（例）、全銀振込結果ファイル取込（例）、日計出力（例） 等 | スキーマ／受渡方式／再処理条件／ファイル形式の契約として扱う |

上記はすべてAPI契約として扱い、本方針の適用対象としなければならない。

---

## 第6章 API基本方針（DDD/BCとの関係）

### 6.1 DDD／コンテキストマップとの整合

#### 6.1.1 APIとBC境界の基本原則

**表8 — APIとBC境界の基本原則**

| 原則 | 説明 |
|------|------|
| 境界尊重 | APIは、BC内部のドメインモデルを他BCに直接公開してはならない。必要に応じてACL／翻訳層（Anti-Corruption Layer）を設けなければならない |
| 責務分離 | Domain APIは単一BC内部で完結する操作のみを提供し、BC横断の責務はProcess APIに委任しなければならない |
| ユビキタス言語整合 | APIで使用する語彙は、各BCのユビキタス言語およびVO辞書と整合させなければならない |
| アーキテクチャ適合 | API設計はコンテキストマップで定義された関係（ACL／Shared Kernel／Separate Ways 等）と整合していなければならない |

#### 6.1.2 API種別とBC境界の対応

**表9 — API種別とBC境界の対応**

| API種別 | BCとの関係 | 設計上の注意点 |
|---------|------------|----------------|
| Domain API | 単一BC内 | 1つのBC内部のユースケースを集約単位で提供する。BC内部境界を越えてはならない |
| Process API | BC横断 | BC間のオーケストレーションを実装する。リトライ／補償処理もProcess API側で管理しなければならない |
| BFF | BC境界外 | 顧客向けUI／加盟店向けUIのための集約ビュー提供に特化し、ビジネスルールはBCまたはProcess API側に保持しなければならない |
| External Public API | BC外部 | ACLパターンに従いBC外部の境界として扱わなければならない |
| Event API | BC横断（疎結合） | 状態変化をイベントとして発行し、他BCが購読する構造を想定する |
| Batch API | BC横断／外部 | 定期連携やファイル受渡しを担当する。再処理条件やファイル管理は契約に明示しなければならない |

#### 6.1.3 コンテキストマップとの整合ルール

API設計時には、必ずコンテキストマップを参照し、以下を確認しなければならない。

**表10 — コンテキストマップ整合確認項目**

| 確認項目 | 説明 |
|----------|------|
| 境界タイプの確認 | コンテキスト間の関係がACL／Shared Kernel／Separate Waysのどれに該当するかを明確にしなければならない |
| モデル依存の確認 | 他BCのドメインモデルを直接参照する必要がある場合はShared KernelかACLかを判断しなければならない |
| イベント共有の可否 | イベント共有が発生する箇所について、イベント形式とVOの整合性を保証しなければならない |
| 変更影響管理 | API変更が他BCまたは外部システムに影響を与える場合、影響範囲を洗い出しレビューを行わなければならない |

### 6.2 API種別ごとの責務・設計原則

**表11 — API種別ごとの責務・設計原則**

| API種別 | 責務 | 設計原則 |
|---------|------|----------|
| Domain API | 集約／ユースケース | 集約の不変条件を守り、DDDモデルと整合したAPI設計でなければならない。1つのDomain APIで複数BCの責務を扱ってはならない |
| Process API | 業務フロー | BC横断の調整を担い、業務フロー単位で契約を定義しなければならない。Saga／補償トランザクション等の制御もProcess API側で明確化しなければならない |
| BFF | UI適合 | UI専用APIとして、ビジネスロジックを含んではならない。レスポンス整形・集約・フィルタリングなどプレゼンテーションロジックに限定しなければならない |
| External Public API | 外部提供 | 公開レベル（Public／Partner／Internal）を区分管理しなければならない。契約やSLA、利用制約を明示しなければならない |
| Event API | 状態通知 | イベント名・契機はイベントストーミング定義と整合しなければならない。重要イベントについてはバージョニングとスキーマ進化方針を定めなければならない |
| Batch API | データ交換 | ファイル形式とスキーマ、検証、再処理条件を含む契約を明示しなければならない |

---

## 第7章 APIライフサイクル管理方針

### 7.1 ライフサイクルフェーズ

**表12 — APIライフサイクルフェーズ**

| フェーズ | 説明 | 必須アウトプット |
|----------|------|------------------|
| 企画 | API追加の目的・ビジネス価値を明確化し、API種別を判定する | API企画書 |
| 設計 | API契約（仕様）を定義し、形式と公開レベルを設計する。仕様書はレビューを完了しなければならない | API仕様書（OpenAPI/AsyncAPI） |
| 実装・テスト | API仕様に基づいて実装し、機能・性能・セキュリティ要件を検証しなければならない | 実装コード、テスト結果 |
| リリース | 本番環境へのデプロイと公開範囲の設定を行い、APIポートフォリオを更新しなければならない | リリース記録、APIカタログ更新記録 |
| 廃止 | API廃止やバージョン削除に際し、利用者への通知・移行期間・代替APIを定義しなければならない | 廃止計画・告知記録 |

### 7.2 バージョニング方針

**表13 — バージョニング方針**

| 項目 | 要求事項 |
|------|----------|
| バージョン表現 | URIパスにメジャーバージョンを含める（例：`/api/v1/contracts`）。マイナーバージョンはヘッダで表現してもよい |
| 後方互換 | 互換性を破る変更はメジャーバージョンアップとし、旧バージョンは最低6ヶ月間並行提供しなければならない |
| 廃止告知 | 廃止時は、少なくとも3ヶ月以上前に利用者（内部・外部）に通知しなければならない |
| スキーマ進化 | 後方互換な修正（フィールド追加等）は、スキーマの互換性検証を通過しなければならない |
| セマンティックバージョニング | APIバージョンはセマンティックバージョニング（MAJOR.MINOR.PATCH）に従うべきである |

---

## 第8章 API仕様標準方針

### 8.1 仕様形式・管理方法

**表14 — 仕様形式・管理方法**

| 項目 | 記述内容 |
|------|----------|
| 同期API仕様形式 | OpenAPI 3.0（YAML形式）を採用する |
| 非同期API仕様形式 | AsyncAPI 2.0を採用する |
| 管理リポジトリ | API仕様はGitで管理し、変更履歴を追跡可能としなければならない |
| レビュー要件 | API仕様の新規作成・変更は、アーキテクト・ドメインエキスパートのレビューを通過しなければならない |
| 契約テスト | Consumer-Driven Contract Testingを導入し、BC間のAPI契約を自動検証すべきである |

### 8.2 命名規約・URI設計

**表15 — 命名規約・URI設計**

| 項目 | 要求事項 |
|------|----------|
| ベースパス | `/api/{version}/{bc-name}/` の形式で統一しなければならない |
| リソース名 | ケバブケース（kebab-case）・複数形で統一しなければならない（例：`/contracts`, `/payment-authorizations`） |
| フィールド名 | キャメルケース（camelCase）で統一しなければならない。ユビキタス言語VO定義書に基づき命名すること |
| アクション表現 | RESTfulな設計を基本とし、リソース操作はHTTPメソッドで表現しなければならない |
| クエリパラメータ | フィルタリング・ページング・ソートはクエリパラメータで表現しなければならない |

### 8.3 HTTPステータスコード規約

**表16 — HTTPステータスコード規約**

| ステータスコード | 用途 | 使用場面 |
|-----------------|------|---------|
| 200 OK | 成功（リソース返却あり） | GET成功、PUT/PATCH成功（更新後リソース返却） |
| 201 Created | リソース作成成功 | POST成功（新規作成） |
| 204 No Content | 成功（リソース返却なし） | DELETE成功、PUT成功（返却不要） |
| 400 Bad Request | リクエスト形式エラー | バリデーションエラー、必須パラメータ不足 |
| 401 Unauthorized | 認証エラー | 認証トークン無効・期限切れ |
| 403 Forbidden | 認可エラー | 権限不足 |
| 404 Not Found | リソース未存在 | 指定IDのリソースが存在しない |
| 409 Conflict | 競合エラー | 楽観ロック失敗、状態遷移不正 |
| 422 Unprocessable Entity | 業務ルールエラー | ビジネスルール違反（バリデーションは通過） |
| 429 Too Many Requests | レートリミット超過 | スロットリング発動時 |
| 500 Internal Server Error | サーバー内部エラー | 予期しない例外 |
| 503 Service Unavailable | サービス利用不可 | メンテナンス中、依存サービス障害 |

### 8.4 冪等性規約

#### 8.4.1 冪等性の基本原則

**表17 — 冪等性の基本原則**

| 原則 | 説明 |
|------|------|
| 冪等キー必須 | 更新系API（POST、PUT、PATCH、DELETE）には `Idempotency-Key` ヘッダを必須としなければならない |
| 重複検出 | サーバーは冪等キーに基づく重複リクエストを検出し、初回と同じレスポンスを返さなければならない |
| 保存期間 | 冪等キーは最低24時間保存しなければならない（業務要件に応じて延長可） |
| 再送前提設計 | 端末/ネットワーク都合のタイムアウト→再送を前提とした設計としなければならない |

#### 8.4.2 冪等キーの仕様

**表18 — 冪等キーの仕様**

| 項目 | 仕様 |
|------|------|
| ヘッダ名 | `Idempotency-Key` |
| 形式 | UUID v4を推奨。クライアントが生成しなければならない |
| 有効期間 | 24時間（デフォルト）。APIごとに延長可 |
| 重複時レスポンス | 初回処理と同じステータスコード・ボディを返却する |
| 処理中の重複 | 初回処理が進行中の場合は `409 Conflict` を返却する |

#### 8.4.3 重複リクエスト時の扱い

**表19 — 重複リクエスト時の扱い**

| パターン | 説明 | 適用場面 |
|---------|------|----------|
| 成功扱い | 重複リクエストを成功として処理し、初回と同じレスポンスを返す | 決済承認、契約申込 |
| 無視 | 重複リクエストを無視し、204 No Contentを返す | 通知、ログ出力 |
| 整合修復 | 重複検出時に整合性を確認し、必要に応じて修復する | 在庫更新、残高更新 |

### 8.5 エラーレスポンス標準

#### 8.5.1 エラーレスポンス形式

すべてのAPIエラーは以下の標準形式で返却しなければならない。

```json
{
  "error": {
    "code": "CONTRACT_LIMIT_EXCEEDED",
    "message": "契約限度額を超過しています",
    "details": [
      {
        "field": "amount",
        "reason": "利用限度額500,000円を超過しています",
        "rejectedValue": 600000
      }
    ],
    "retryable": false,
    "timestamp": "2026-01-15T10:30:00+09:00",
    "traceId": "abc123-def456-ghi789"
  }
}
```

#### 8.5.2 エラー分類

**表20 — エラー分類**

| 分類 | error.code形式 | HTTPステータス | 再試行可否 | 説明 |
|------|---------------|---------------|-----------|------|
| バリデーションエラー | `VALIDATION_*` | 400 | 不可 | リクエスト形式・必須項目の不備 |
| 認証エラー | `AUTH_*` | 401 | 不可（再認証必要） | 認証トークンの問題 |
| 認可エラー | `AUTHZ_*` | 403 | 不可 | 権限不足 |
| リソース未存在 | `NOT_FOUND_*` | 404 | 不可 | 指定リソースが存在しない |
| 業務ルールエラー | `BUSINESS_*` | 422 | 不可 | ビジネスルール違反 |
| 競合エラー | `CONFLICT_*` | 409 | 条件付き可 | 楽観ロック失敗、状態遷移不正 |
| レートリミット | `RATE_LIMIT_*` | 429 | 可（待機後） | スロットリング発動 |
| システムエラー | `SYSTEM_*` | 500 | 可（バックオフ） | サーバー内部エラー |
| サービス利用不可 | `SERVICE_*` | 503 | 可（バックオフ） | 依存サービス障害 |

#### 8.5.3 リトライ方針

**表21 — リトライ方針**

| 条件 | リトライ可否 | 推奨方針 |
|------|------------|---------|
| 4xx系エラー（400, 401, 403, 404, 422） | 不可 | 即座に失敗として処理 |
| 409 Conflict | 条件付き可 | 最新状態を取得後に再試行 |
| 429 Too Many Requests | 可 | `Retry-After` ヘッダの値に従い待機後再試行 |
| 500 Internal Server Error | 可 | Exponential Backoff（初回1秒、最大32秒、最大5回） |
| 503 Service Unavailable | 可 | `Retry-After` ヘッダがあれば従い、なければExponential Backoff |
| タイムアウト | 可 | 冪等キー付きで再試行 |

---

## 第9章 APIセキュリティ・アクセス制御方針

本章は「セキュリティ方針」「セキュリティ非機能要件定義書」の参照が主であり、API固有の補足のみを記載する。

### 9.1 認証・認可の適用

**表22 — 認証・認可の適用**

| 項目 | 要求事項 |
|------|----------|
| 認証方式 | 具体的な方式（OIDC／OAuth2.0／Mutual TLS／Basic認証等）はセキュリティ方針を参照すること。外部公開APIは認証必須としなければならない |
| 認可スコープ | API単位で必要な権限（読取／更新／管理等）を定義し、API仕様書に明示しなければならない |
| ゼロトラスト | 内部APIであっても、ネットワーク境界やBC境界を越える通信には認証と認可を適用しなければならない |

### 9.2 伝送路・入力検証

**表23 — 伝送路・入力検証**

| 項目 | 要求事項 |
|------|----------|
| 通信経路の保護 | TLS等の暗号化方式はセキュリティ方針を参照し、すべてのAPI通信がその要件を満たさなければならない |
| 入力検証 | API入力はスキーマに基づいてサーバ側で検証し、不正入力を拒否しなければならない |
| 機微情報の取扱い | 個人情報・金融情報等の機微データのマスキング／ログ抑止／暗号化要件はセキュリティ方針を参照しなければならない |

### 9.3 機微データ排除規約

#### 9.3.1 禁止データの定義

**表24 — 禁止データ定義**

| 分類 | データ例 | 扱い |
|------|---------|------|
| 禁止データ | カード番号（PAN）、CVV、暗証番号 | APIリクエスト/レスポンス、ログ、仕様書サンプルに含めてはならない。トークン化必須 |
| 要マスキング | 氏名、住所、電話番号、メールアドレス | ログ出力時はマスキング必須。APIレスポンスでは必要最小限に留める |
| 要暗号化 | 口座番号、生年月日 | 保存時は暗号化必須 |
| 一般データ | 契約ID、取引ID、金額 | 通常の扱い |

#### 9.3.2 API仕様書における機微データ排除

**表25 — API仕様書における機微データ排除規約**

| 対象 | 規約 |
|------|------|
| OpenAPI仕様のサンプル値 | 禁止データを含むサンプル値を記載してはならない。テスト用トークンまたはダミー値を使用すること |
| テストデータ | 本番の禁止データをテストに使用してはならない。専用のテストデータセットを使用すること |
| ログ出力 | 禁止データ・要マスキングデータをログに平文で出力してはならない |
| エラーレスポンス | エラー詳細に禁止データを含めてはならない |
| APIドキュメント | 禁止データの具体的な値を例示してはならない |

#### 9.3.3 参照ID方式

機微データが必要な場合は、参照ID経由で必要な時点でのみ取得する方式を採用しなければならない。

**表26 — 参照ID方式**

| 原則 | 説明 |
|------|------|
| 参照ID返却 | APIレスポンスには機微データ本体ではなく、参照ID（トークン）を返却する |
| 別API経由取得 | 機微データ本体が必要な場合は、専用の参照APIを呼び出して取得する |
| アクセス制御 | 機微データ参照APIには厳格な認可制御を適用しなければならない |
| 監査ログ | 機微データへのアクセスは監査ログに記録しなければならない |

---

## 第10章 API品質・非機能方針

数値基準は「非機能要件定義書」「性能定義書」を参照すること。

### 10.1 性能・可用性・スロットリング

**表27 — 性能・可用性・スロットリング**

| 項目 | 要求事項 |
|------|----------|
| 性能基準の参照 | 各APIは非機能要件定義書の性能目標を参照し、それに基づき設計しなければならない |
| スロットリング | 外部公開APIに対してはスロットリング／レートリミット方針を定義しなければならない。デフォルトは1000リクエスト/分/クライアント |
| 可用性 | 可用性の目標値は性能定義書に従い、本書では「当該値を満たす設計義務」を定める |
| タイムアウト | クライアント側タイムアウトは30秒、サーバー側タイムアウトは60秒をデフォルトとする |

### 10.2 可観測性・ログ

**表28 — 可観測性・ログ**

| 項目 | 要求事項 |
|------|----------|
| メトリクス | APIリクエスト数、エラー率、レイテンシ等を収集しなければならない |
| トレース | 分散トレーシングを適用し、全APIで一貫したトレースIDを伝播しなければならない |
| ログ方針 | APIアクセスログ・監査ログの項目・保管期間はロギング／監査方針書を参照しなければならない |
| ヘルスチェック | 各APIサービスはヘルスチェックエンドポイント（`/health`）を提供しなければならない |

---

## 付録A 未確定事項一覧

本方針書において「未確定」と記載された事項を以下にまとめる。これらは後続の検討・合意形成により確定させなければならない。

**表A.1 — 未確定事項一覧**

| 章節 | 項目 | 備考 |
|------|------|------|
| 1.2 | 対象BC一覧 | コンテキストマップおよびドメインスコープ定義書の策定完了後に確定 |
| 1.2 | PoC／一時検証APIの例外承認ルール | 詳細運用ルールの策定が必要 |

---

## 付録B 検討が必要な論点

以下は、本方針書の運用にあたり検討が必要な論点である。

1. **API設計レビュープロセスの詳細化**
   - レビュー参加者（アーキテクト、セキュリティ担当、ドメインエキスパート等）の明確化
   - レビュー観点チェックリストの作成

2. **APIカタログ管理ツールの選定**
   - API仕様の一元管理・検索・可視化ツールの検討

3. **契約テスト（Consumer-Driven Contract Testing）の導入**
   - BC間のAPI契約を自動検証する仕組みの検討
   - Pact等のツール選定

4. **APIゲートウェイの導入範囲**
   - 認証・レートリミット・ルーティングの一元化範囲の検討

---

## 付録C OpenAPI記述例

ハウスクレジットシステムにおけるOpenAPI記述例を以下に示す。

```yaml
openapi: 3.0.3
info:
  title: 契約BC API
  description: ハウスクレジット契約管理API
  version: 1.0.0
servers:
  - url: https://api.example.com/api/v1/contract
    description: Production server

paths:
  /contracts:
    post:
      summary: 契約申込
      operationId: createContract
      tags:
        - contracts
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          schema:
            type: string
            format: uuid
          description: 冪等キー（クライアント生成UUID）
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateContractRequest'
      responses:
        '201':
          description: 契約作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContractResponse'
        '400':
          $ref: '#/components/responses/BadRequest'
        '422':
          $ref: '#/components/responses/BusinessError'

  /contracts/{contractId}:
    get:
      summary: 契約照会
      operationId: getContract
      tags:
        - contracts
      parameters:
        - name: contractId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 契約情報
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ContractResponse'
        '404':
          $ref: '#/components/responses/NotFound'

components:
  schemas:
    CreateContractRequest:
      type: object
      required:
        - customerId
        - productType
        - creditLimit
      properties:
        customerId:
          type: string
          description: 顧客ID
          example: "CUST-001"
        productType:
          type: string
          enum: [SHOPPING_LOAN, REVOLVING]
          description: 商品種別
        creditLimit:
          type: integer
          minimum: 10000
          maximum: 5000000
          description: 利用限度額（円）
          example: 500000

    ContractResponse:
      type: object
      properties:
        contractId:
          type: string
          description: 契約ID
          example: "CONTRACT-001"
        customerId:
          type: string
          description: 顧客ID
        status:
          type: string
          enum: [APPLYING, ACTIVE, TERMINATED]
          description: 契約ステータス
        creditLimit:
          type: integer
          description: 利用限度額
        createdAt:
          type: string
          format: date-time
          description: 作成日時

    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              description: エラーコード
            message:
              type: string
              description: エラーメッセージ
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  reason:
                    type: string
                  rejectedValue:
                    type: string
            retryable:
              type: boolean
              description: 再試行可能か
            timestamp:
              type: string
              format: date-time
            traceId:
              type: string

  responses:
    BadRequest:
      description: リクエスト形式エラー
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error:
              code: "VALIDATION_ERROR"
              message: "リクエストの形式が不正です"
              details:
                - field: "creditLimit"
                  reason: "必須項目です"
              retryable: false
              timestamp: "2026-01-15T10:30:00+09:00"
              traceId: "abc123"

    BusinessError:
      description: 業務ルールエラー
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error:
              code: "BUSINESS_CREDIT_LIMIT_EXCEEDED"
              message: "利用限度額が上限を超えています"
              retryable: false
              timestamp: "2026-01-15T10:30:00+09:00"
              traceId: "abc123"

    NotFound:
      description: リソース未存在
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            error:
              code: "NOT_FOUND_CONTRACT"
              message: "指定された契約が存在しません"
              retryable: false
              timestamp: "2026-01-15T10:30:00+09:00"
              traceId: "abc123"

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```

---

## 付録D Spring Boot実装例

### D.1 Controllerの実装例

```java
@RestController
@RequestMapping("/api/v1/contract/contracts")
@RequiredArgsConstructor
public class ContractController {

    private final CreateContractUseCase createContractUseCase;
    private final GetContractUseCase getContractUseCase;

    @PostMapping
    public ResponseEntity<ContractResponse> createContract(
            @RequestHeader("Idempotency-Key") String idempotencyKey,
            @Valid @RequestBody CreateContractRequest request) {
        
        ContractResponse response = createContractUseCase.execute(
            idempotencyKey, 
            request.toCommand()
        );
        
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{contractId}")
    public ResponseEntity<ContractResponse> getContract(
            @PathVariable String contractId) {
        
        ContractResponse response = getContractUseCase.execute(contractId);
        return ResponseEntity.ok(response);
    }
}
```

### D.2 エラーハンドリングの実装例

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(
            BusinessException ex, HttpServletRequest request) {
        
        ErrorResponse response = ErrorResponse.builder()
            .code(ex.getErrorCode())
            .message(ex.getMessage())
            .retryable(false)
            .timestamp(Instant.now())
            .traceId(MDC.get("traceId"))
            .build();
        
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
            .body(response);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(
            MethodArgumentNotValidException ex) {
        
        List<ErrorDetail> details = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(e -> new ErrorDetail(
                e.getField(), 
                e.getDefaultMessage(), 
                e.getRejectedValue()
            ))
            .collect(Collectors.toList());
        
        ErrorResponse response = ErrorResponse.builder()
            .code("VALIDATION_ERROR")
            .message("リクエストの形式が不正です")
            .details(details)
            .retryable(false)
            .timestamp(Instant.now())
            .traceId(MDC.get("traceId"))
            .build();
        
        return ResponseEntity.badRequest().body(response);
    }
}
```

---

## 改版履歴

| 版数 | 日付 | 変更内容 | 作成者 |
|------|------|---------|--------|
| 1.0 | 2026-01-14 | 初版作成 | - |
| 1.1 | 2026-01-15 | 技術スタック追加、冪等性規約追加、エラーレスポンス標準追加、機微データ排除規約追加、具体例追加 | - |

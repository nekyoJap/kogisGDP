:::callout
要件定義工程で作成する成果物には成果物IDを付与する。本ドキュメントでは成果物IDの採番ルールについて説明する。

:::

# 1.採番ルール

以下の通り成果物・ドメイン・BCにそれぞれ略称を定義し、連番を割り振ることでトレーサビリティや検索性、管理効率を確保する。

```auto
<成果物略称3桁><ドメイン略称2桁><BC略称2桁><連番3桁>_<成果物名>(_<ドメイン名>or<BC名>※ドメイン/BC単位で作成する成果物の場合は付与)
```
| 種類 | 説明 | 例 |
|----|----|---|
| 成果物略称 | ビジネスビジョンステートメントなど成果物の略称 | BVS(ビジネスビジョンステートメント/Business Vision Statement) |
| ドメイン略称 | 審査発行管理、顧客管理などドメイン定義の略称 | CM（顧客管理/Customer Management） |
| BC略称 | ドメイン内で境界定義されたコンテキスト(BC)定義の略称 | CV（顧客審査/Customer Verification |
| 成果物名 | 成果物の名称 | ドメインスコープ定義書 |

# 2.成果物略称一覧
| 略称 | 成果物 | 由来する英単語 |
|----|-----|---------|
| BVS | ビジネスビジョンステートメント | Business Vision Statement |
| DSD | ドメインスコープ定義書 | Domain Scope Definition |
| BFL | ビジネスフロー | Business Flow |
| ESD | イベントストーミング図 | Event Storming Diagram |
| DRL | ドメインビジネスルール一覧 | Domain Rule List |
| DRD | ドメインビジネスルール詳細 | Domain Rule Details |
| GLO | 表記語集 | Glossary |
| CXM | コンテキストマップ | Context Map |
| CXL | コンテキスト一覧 | Context List |
| AUP | 認証・認可方針書 | Auth (Authentication/z) Policy |
| TXP | トランザクション方針書 | Transaction Policy |
| EXP | 例外処理ポリシー | Exception Policy |
| SCP | セキュリティ方針書 | Security Policy |
| AGP | APIガバナンス方針書 | API Governance Policy |
| AIP | 非同期連携方針 | Async Integration Policy |
| ALP | アプリケーションログ方針書 | App Log Policy |
| TQP | テスト・品質保証方針書 | Test / QA Policy |
| ARC | アーキテクチャ方針書 | Architecture Policy |
| DMP | データモデリング方針書 | Data Modeling Policy |
| BCO | BC概要書 | BC Overview |
| BCG | BC Gherkin | BC Gherkin |
| CDE | コード定義 | Code Definition |
| UBL | ユビキタス言語 | Ubiquitous Language |
| AGL | 集約一覧 | Aggregate List |
| AGG | 集約Gherkin | Aggregate Gherkin |
| AGS | 集約仕様書 | Aggregate Specification |
| DSL | ドメインサービス一覧 | Domain Service List |
| DSG | ドメインサービスGherkin | Domain Service Gherkin |
| DSS | ドメインサービス仕様書 | Domain Service Specification |
| VOD | VO定義書 | Value Object Definition |
| DEL | ドメインイベント一覧 | Domain Event List |
| DES | ドメインイベント仕様書 | Domain Event Specification |
| OPL | OutBoxポート一覧 | OutBox Port List |
| OPS | OutBoxポート仕様書 | OutBox Port Specification |
| RPL | リポジトリポート一覧 | Repository Port List |
| RPS | リポジトリポート仕様書 | Repository Port Specification |
| CML | コマンド一覧 | Command List |
| CMG | コマンドGherkin | Command Gherkin |
| CMS | コマンド仕様書 | Command Specification |
| QRL | クエリ一覧 | Query List |
| QRG | クエリGherkin | Query Gherkin |
| QRS | クエリ仕様書 | Query Specification |
| PJL | プロジェクション一覧 | Projection List |
| PJS | プロジェクション仕様書 | Projection Specification |
| OAL | OutBoxアダプター一覧 | OutBox Adapter List |
| OAS | OutBoxアダプタ仕様書 | OutBox Adapter Specification |
| RAL | リポジトリアダプター一覧 | Repository Adapter List |
| RAS | リポジトリアダプタ仕様書 | Repository Adapter Specification |
| TLA | テーブル一覧（Aurora） | Table List (Aurora) |
| TSA | テーブル仕様書（Aurora） | Table Specification (Aurora) |
| TLD | テーブル一覧（Dynamo） | Table List (Dynamo) |
| TSD | テーブル仕様書（Dynamo） | Table Specification (Dynamo) |
| APL | API一覧表 | API List |
| APS | API仕様書 | API Specification |
| ECL | 外部接続一覧 | External Connection List |
| ECS | 外部接続仕様書 | External Connection Spec |
| MSL | メッセージ一覧 | Message List |
| BIL | BC間連携一覧 | BC Integration List |
| BIS | BC間連携仕様書 | BC Integration Spec |
| RTL | 帳票一覧 | Report List |
| RTS | 帳票仕様書 | Report Specification |
| RTM | 帳票モック | Report Mock |
| BTL | バッチ一覧 | Batch List |
| BTS | バッチ仕様書 | Batch Specification |
| SCL | 画面一覧 | Screen List |
| SCS | 画面仕様書 | Screen Specification |
| SCM | 画面モック | Screen Mock |
| STD | 画面遷移図 | Screen Transition Diagram |
| SNR | セキュリティ非機能要求定義書 | Security Non-func Req |
| LAP | ロギング／監査方針書 | Logging / Audit Policy |
| PFR | 性能要件定義書 | Performance Requirement |
| IAC | システム／IaC構成定義書 | System / IaC Config |
| ALL | 監査／業務ログ一覧 | Audit / Biz Log List |
| OPR | 運用要件定義書 | Operation Requirement |
| MGR | 移行要件定義書 | Migration Requirement |

# 3.ドメイン略称一覧
| 略称 | ドメイン | 由来する英単語 |
|----|------|---------|
| ZZ | 全ドメイン共通 | \- |
| IS | 審査発行管理 | Issuing |
| CS | 顧客管理 | Customer |
| AU | カード利用 | Authorization / Auth |
| SL | 売上管理 | Sales |
| MC | 加盟店契約管理 | Merchant |
| MS | 加盟店精算管理 | Merchant Settlement |
| PD | 商品管理 | Product |
| BL | 会員精算管理 | Billing |
| RC | 債権管理 | Receivables |
| PT | ポイント管理 | Point |
| CP | キャンペーン管理 | Campaign |
| AC | 会計統合管理 | Accounting |
| CM | 共通運用管理 | Common |

# 4.BC略称一覧

:::callout
BC定義後に略称も定義し、以下へ追加予定。

:::
| 略称 | BC | 由来する英単語 |
|----|----|---------|
| ZZ | 共通 | \- |
| CV | 顧客審査 | Customer Verification |
|  |  |  |

# 5.採番例
| 成果物 | 作成単位 | 例 |
|-----|------|---|
| ビジネスビジョンステートメント | システム全体 | **BVSZZZZ001\_ビジネスビジョンステートメント** |
| イベントストーミング図 | ドメイン | **ESDISZZ001\_イベントストーミング図\_審査発行管理**<br>**ESDCSZZ001\_イベントストーミング図\_顧客管理** |
| BC概要書 | BC | **BCOISCV001_BC概要書\_顧客審査** |


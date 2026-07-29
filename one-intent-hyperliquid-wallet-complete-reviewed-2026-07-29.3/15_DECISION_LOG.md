# Architecture Decision Log

## ADR-001 独立Android／iPhoneネイティブアプリ

**決定:** ChatGPT Appではなく独立アプリ。  
**理由:** ChatGPT内の金融・暗号資産取引実行制限、端末署名、緊急導線。  
**結果:** ChatGPT integrationは、抽象read-only状態、固定用語・エラー、一般安全案内、固定中立handoffだけ。

## ADR-002 取引Parserは未信頼Draftのみ

**決定:** 端末内決定論parserを第一候補とし、必要時も独立運用の非OpenAIコンポーネントだけを候補にする。実行toolを与えない。  
**理由:** 誤解析、input injection、policy。  
**結果:** 独立ウォレットの具体的ボタンが実行起点。

## ADR-003 Execution Capsule

**決定:** 画面・認証・署名をcanonical dataへ結び付ける。  
**理由:** UI/payload mismatch防止。

## ADR-004 Saga

**決定:** 複合処理を非原子的Sagaとして扱う。  
**理由:** HyperCore／Bridge／EVMを跨ぐ。

## ADR-005 Agentを限定権限と見なさない

**決定:** protocol scopeではなくdefense-in-depth。  
**理由:** approveAgentに細粒度scopeがない。

## ADR-006 Existing Wallet First

**決定:** Testnet基準はexisting wallet。  
**理由:** MPC採用前にbusiness logicを検証。

## ADR-007 MPC Conditional

**決定:** 監査・復旧・法務が揃った場合のみ。  
**理由:** MPCは魔法の非カストディ判定ではない。

## ADR-008 No arbitrary EVM calls

**決定:** selector／contract allowlist。  
**理由:** generic wallet化による攻撃面拡大。

## ADR-009 Dynamic metadata

**決定:** token、tick、lot、fee、Bridge状態をruntime検証。  
**理由:**仕様変更。

## ADR-010 Feature-gated all-in scope

**決定:** 全機能を設計・実装対象、Mainnet有効化は個別。  
**理由:** ユーザー要求と安全性を両立。

## ADR-011 Trusted Display分離

**決定:** BiometricPromptを取引内容のTrusted Displayとみなさない。  
**結果:** R4とstanding例外を満たさないR3はProtected Confirmation、外部wallet、hardware wallet、またはNO_GO。R3 app内例外は事前R4 ceremony＋cooling＋hard cap付き。

## ADR-012 Independent State Evidence

**決定:** critical stateを単一APIへ依存しない。  
**結果:** R2以上は独立source照合、Signer再検証、divergence fail-closed。

## ADR-013 Agent Bearer Credential

**決定:** product signer allowlistはagent key漏えい後のprotocol scopeにならない。  
**結果:** dedicated exposure、characterization、monitor、revokeを必須化。

## ADR-014 Environment-specific Test Gates

**決定:** HyperCore Testnet、Bridge fork、HyperEVM fork、Mainnet canaryを分離。  
**理由:** Testnet成功はMainnet完全同等性を証明しない。

## ADR-015 Store Distribution Gate

**決定:** Google Play申告・crypto policy・地域適格性をpublic release blockerとする。

## ADR-016 One Intent ≠ One Signature

**決定:** UX上の1つのIntentと、chain／wallet上の署名回数を分離する。  
**理由:** Existing Wallet Modeのroot actionや動的Sagaは複数署名を必要とし得る。  
**結果:** 完全なアプリ内1回認証は、監査済みManaged Self-Custody Modeのみ。

## ADR-017 Authorization Envelope

**決定:** `semanticHash`、`renderReceiptHash`、`sourceStateHash`、`promptTextHash`、challenge、presentation modeを一つのAuthorization Envelopeへ束縛する。  
**理由:** Capsule hashだけではTrusted Displayの表示内容やstate evidenceの派生hashを取り違え得る。

## ADR-012 Native shells＋shared pure core

Flutter／React Native一枚構成を採らず、AndroidはCompose、iOSはSwiftUIとする。共通化はpure coreに限定する。理由はKeystore、Protected Confirmation、Secure Enclave、App Attest、LocalAuthenticationの保証差を隠さないため。

## ADR-013 iOS authenticated UI is not trusted display

`IOS_APP_ATTESTED_AUTHENTICATED_UI`を定義し、`trustedDisplayClaim=false`を機械的に強制する。

## ADR-014 Public iOS distribution default OFF

organization／license／legal／App Review evidenceが揃うまでApp Store public gateを開かない。

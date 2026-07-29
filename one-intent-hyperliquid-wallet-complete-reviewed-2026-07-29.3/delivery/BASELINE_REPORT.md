# Baseline report — 2026-07-29.3

## 固定したbaseline

既存 `.2` packageを直接変更せず、ZIP SHA-256、manifest、SHA256SUMS、clean-extract tree digestを固定した。親Git worktreeは開始時点でdirtyだったため、既存変更を戻さず、`.2`を入力として新しい`.3` packageを作成した。

## clean extract再検証

依存関係を持つ隔離Python環境と `PYTHONDONTWRITEBYTECODE=1` を使用し、以下を実行した。

- Python source compile 94件：PASS
- Python unit test 64件：PASS
- local sandbox self-test：PASS
- validation harness：36 assertions PASS
- full non-mutating validation：PASS
- readiness check：`BLOCKED_NOT_OPERATIONAL` を正しく維持してPASS
- source tree前後一致：PASS

初回のsystem Python実行では`jsonschema`等が未導入で失敗した。また、unit testをfull validationより先に同じ展開先で実行した診断では`__pycache__`をvalidatorが拒否した。どちらも原因を隠さず記録し、依存付きfresh extractで再実行している。

## 境界

この結果は、offline design packageの整合性を示す。production backend、signer、HSM/MPC、Testnet/Mainnet、provider契約、法務、Store、独立監査、Mainnet canaryの証拠ではない。最終判定は`BLOCKED_NOT_OPERATIONAL`とする。

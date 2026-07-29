#if canImport(SwiftUI)
import SwiftUI
#if canImport(OfflineWalletContract)
import OfflineWalletContract
#endif

/// UI-only review shell. It never signs, broadcasts, or creates executable links.
public struct ReviewScreen: View {
    public let draft: ReviewContract

    public init(draft: ReviewContract) {
        self.draft = draft
    }

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("オフライン確認")
                    .font(.largeTitle.bold())
                Text("画面例・ライブ送信ではありません")
                    .font(.headline)
                    .foregroundStyle(.tint)
                GroupBox {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("認識した原文")
                            .font(.subheadline.weight(.semibold))
                        Text(draft.sourceUtterance)
                            .font(.body)
                            .accessibilityLabel("認識した原文")
                        Text("読み取り候補")
                            .font(.subheadline.weight(.semibold))
                        Text(draft.normalizedInterpretation)
                            .font(.body)
                            .accessibilityLabel("読み取り候補")
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                Text(draft.materialAmbiguities.isEmpty ? "未確認の項目はありません。" : "未確認: \(draft.materialAmbiguities.joined(separator: "、"))")
                    .accessibilityLabel("未確認の項目")
                    .font(.body)
                Text("判定: \(draft.reasonCode.rawValue)")
                    .font(.headline)
                    .foregroundStyle(draft.primaryActionEnabled ? Color.accentColor : Color.red)
                Button("最終確認へ") { }
                    .frame(maxWidth: .infinity, minHeight: 48)
                    .disabled(!draft.primaryActionEnabled)
                Text("この画面例では署名・送信・deep link実行を行いません。")
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 20)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(Color.secondary.opacity(0.08))
    }
}
#endif

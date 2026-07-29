package jp.offlinewallet

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/** Offline contract shell; no signer, network, or executable deep link. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val draft = ReviewContractV1(
                sourceUtterance = "BTCを500 USDC、ペイパチャルで3倍。生産価格も見せて。",
                normalizedInterpretation = "候補を表示しています。",
                materialAmbiguities = listOf("方向", "ネットワーク"),
            )
            ReviewScreen(
                draft = draft,
            )
        }
    }
}

@Composable
fun ReviewScreen(draft: ReviewContractV1) {
    MaterialTheme {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background,
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .statusBarsPadding()
                    .navigationBarsPadding()
                    .padding(horizontal = 24.dp, vertical = 20.dp),
            ) {
                Text(
                    text = "オフライン確認",
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "画面例・ライブ送信ではありません",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(modifier = Modifier.height(20.dp))

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant,
                    ),
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text(
                            text = "認識した原文",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = draft.sourceUtterance,
                            style = MaterialTheme.typography.bodyLarge,
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "読み取り候補",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = draft.normalizedInterpretation,
                            style = MaterialTheme.typography.bodyLarge,
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = if (draft.materialAmbiguities.isEmpty()) {
                        "未確認の項目はありません。"
                    } else {
                        "未確認: ${draft.materialAmbiguities.joinToString("、")}"
                    },
                    style = MaterialTheme.typography.bodyLarge,
                )
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = "判定: ${draft.reasonCode}",
                    style = MaterialTheme.typography.titleMedium,
                    color = if (draft.primaryActionEnabled) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                )
                Spacer(modifier = Modifier.height(20.dp))
                Button(
                    onClick = {},
                    enabled = draft.primaryActionEnabled,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                ) {
                    Text("最終確認へ")
                }
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "この画面例では署名・送信・deep link実行を行いません。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

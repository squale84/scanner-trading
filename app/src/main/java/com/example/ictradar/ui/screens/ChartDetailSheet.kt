package com.example.ictradar.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.SignalDirection
import com.example.ictradar.data.model.TradingAsset
import com.example.ictradar.ui.components.CandleStickChart
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGold
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentGreenSoft
import com.example.ictradar.ui.theme.AccentPurple
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.AccentRedSoft
import com.example.ictradar.ui.theme.BgCard
import com.example.ictradar.ui.theme.BgElevated
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.BorderSoft
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChartDetailSheet(
    asset: TradingAsset,
    signal: SignalData,
    riskEur: Double,
    onReset: () -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = BgElevated,
        dragHandle = null
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(18.dp)
                .verticalScroll(rememberScrollState())
        ) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = asset.symbol,
                        color = TextMain,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace
                    )

                    // Status Badge
                    val (badgeBg, badgeText, badgeColor) = when (signal.status) {
                        "TP_HIT" -> Triple(AccentGreenSoft, "TP TOUCHÉ", AccentGreen)
                        "SL_HIT" -> Triple(AccentRedSoft, "SL TOUCHÉ", AccentRed)
                        else -> {
                            when (signal.direction) {
                                SignalDirection.BUY -> Triple(AccentGreenSoft, "BUY ACTIF", AccentGreen)
                                SignalDirection.SELL -> Triple(AccentRedSoft, "SELL ACTIF", AccentRed)
                                else -> Triple(BgInset, "STANDBY", TextFaint)
                            }
                        }
                    }

                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(badgeBg)
                            .padding(horizontal = 8.dp, vertical = 3.dp)
                    ) {
                        Text(
                            text = badgeText,
                            color = badgeColor,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.ExtraBold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Text(
                        text = asset.tvSymbol,
                        color = TextFaint,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                IconButton(
                    onClick = onDismiss,
                    modifier = Modifier.testTag("close_chart_modal_btn")
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Fermer",
                        tint = TextMuted
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Candlestick technical chart with TP/Entry/SL levels
            CandleStickChart(
                asset = asset,
                signal = signal
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Setup breakdown cards
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    text = "DÉTAILS DU SETUP INSTITUTIONNEL",
                    color = TextMuted,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.6.sp
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Pattern ICT", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = signal.setupIctLabel(),
                        color = TextMain,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Qualité Setup", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = "${signal.quality} ${signal.grade}",
                        color = if (signal.quality == "A+") AccentPurple else AccentBlue,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Ratio R:R", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = if (signal.rr != "0.0") "${signal.rr}:1" else "--",
                        color = TextMain,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(BorderSoft)
                )

                // Price levels
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Niveau d'Entrée", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = signal.entryPrice?.let { String.format(Locale.US, "%.${asset.decimals}f", it) } ?: "--",
                        color = TextMain,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.SemiBold
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Stop Loss (SL)", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = signal.slPrice?.let { String.format(Locale.US, "%.${asset.decimals}f", it) } ?: "--",
                        color = AccentRed,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Take Profit (TP)", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = signal.tpPrice?.let { String.format(Locale.US, "%.${asset.decimals}f", it) } ?: "--",
                        color = AccentGreen,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Prix Actuel", color = TextMuted, fontSize = 12.sp)
                    Text(
                        text = signal.currentPrice?.let { String.format(Locale.US, "%.${asset.decimals}f", it) } ?: "--",
                        color = TextMain,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(BorderSoft)
                )

                // Progress to TP
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Progression vers TP", color = TextMuted, fontSize = 11.sp)
                        Text(
                            text = "${signal.progress}%",
                            color = AccentGreen,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(6.dp)
                            .clip(RoundedCornerShape(3.dp))
                            .background(BgInset)
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth((signal.progress / 100f).coerceIn(0f, 1f))
                                .height(6.dp)
                                .background(
                                    Brush.horizontalGradient(
                                        listOf(AccentBlue, AccentGreen)
                                    )
                                )
                        )
                    }
                }

                // Sizing
                val size = signal.suggestedSize(riskEur)
                if (size != null) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Taille indicative (${riskEur.toInt()} €)", color = TextMuted, fontSize = 12.sp)
                        Text(
                            text = "${String.format(Locale.US, "%.2f", size)} unités",
                            color = AccentGold,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                if (signal.isActive || signal.isExit) {
                    Button(
                        onClick = {
                            onReset()
                            onDismiss()
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = BgInset,
                            contentColor = AccentRed
                        ),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .weight(1f)
                            .border(1.dp, AccentRed.copy(alpha = 0.4f), RoundedCornerShape(8.dp))
                    ) {
                        Text("✕ Réinitialiser")
                    }
                }

                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AccentBlue,
                        contentColor = TextMain
                    ),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Fermer")
                }
            }
        }
    }
}

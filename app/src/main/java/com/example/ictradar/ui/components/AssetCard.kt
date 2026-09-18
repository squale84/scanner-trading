package com.example.ictradar.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.ShowChart
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.SignalDirection
import com.example.ictradar.data.model.TradingAsset
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentBlueSoft
import com.example.ictradar.ui.theme.AccentGold
import com.example.ictradar.ui.theme.AccentGoldSoft
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentGreenSoft
import com.example.ictradar.ui.theme.AccentPurple
import com.example.ictradar.ui.theme.AccentPurpleSoft
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.AccentRedSoft
import com.example.ictradar.ui.theme.BgCard
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.BorderSoft
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AssetCard(
    asset: TradingAsset,
    signal: SignalData,
    riskEur: Double,
    onReset: () -> Unit,
    onOpenChart: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isBuy = signal.direction == SignalDirection.BUY
    val isSell = signal.direction == SignalDirection.SELL
    val isTp = signal.status == "TP_HIT"
    val isSl = signal.status == "SL_HIT"

    val borderColor by animateColorAsState(
        targetValue = when {
            isTp -> AccentGreen
            isSl -> AccentRed
            isBuy -> AccentGreen.copy(alpha = 0.6f)
            isSell -> AccentRed.copy(alpha = 0.6f)
            else -> BorderColor
        },
        label = "borderColor"
    )

    val progressAnim by animateFloatAsState(
        targetValue = (signal.progress / 100f).coerceIn(0f, 1f),
        label = "progressAnim"
    )

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(BgCard)
            .border(1.dp, borderColor, RoundedCornerShape(12.dp))
            .padding(14.dp)
            .testTag("asset_card_${asset.symbol}")
    ) {
        Column {
            // Card Top: Symbol + Badge + Reset
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = asset.symbol,
                        color = TextMain,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = asset.name,
                        color = TextMuted,
                        fontSize = 9.5.sp,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    if (signal.isActive || signal.isExit) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(6.dp))
                                .background(BgInset)
                                .border(1.dp, BorderSoft, RoundedCornerShape(6.dp))
                                .clickable { onReset() }
                                .padding(horizontal = 6.dp, vertical = 3.dp)
                                .testTag("reset_${asset.symbol}")
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = Icons.Default.Close,
                                    contentDescription = "Reset",
                                    tint = TextFaint,
                                    modifier = Modifier.size(11.dp)
                                )
                                Spacer(modifier = Modifier.width(2.dp))
                                Text(
                                    text = "Reset",
                                    color = TextFaint,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }
                    }

                    // Status badge
                    StatusBadge(status = signal.status, direction = signal.direction)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Tags row: Quality Grade, Stars, R:R
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                if (signal.quality != "--" && signal.quality.isNotBlank()) {
                    QualityChip(quality = signal.quality)
                }
                if (signal.grade != "--" && signal.grade.isNotBlank()) {
                    GradeChip(grade = signal.grade)
                }
                if (signal.rr != "0.0" && signal.rr.isNotBlank()) {
                    Chip(text = "R:R ${signal.rr}:1")
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Metrics: Entry, SL, TP, Price, Position Size
            Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
                DataRow(
                    label = "Entrée Setup",
                    value = formatNumber(signal.entryPrice, asset.decimals)
                )
                DataRow(
                    label = "Stop Loss (SL)",
                    value = formatNumber(signal.slPrice, asset.decimals),
                    valueColor = AccentRed
                )
                DataRow(
                    label = "Objectif TP",
                    value = formatNumber(signal.tpPrice, asset.decimals),
                    valueColor = AccentGreen
                )
                DataRow(
                    label = "Dernier Prix",
                    value = formatNumber(signal.currentPrice, asset.decimals)
                )

                val size = signal.suggestedSize(riskEur)
                if (size != null && signal.isActive) {
                    DataRow(
                        label = "Taille indicative",
                        value = "${String.format("%.2f", size)} u.",
                        valueColor = AccentGold
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Progress bar to TP
            Column {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(5.dp)
                        .clip(RoundedCornerShape(3.dp))
                        .background(BgInset)
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth(progressAnim)
                            .height(5.dp)
                            .background(
                                Brush.horizontalGradient(
                                    listOf(AccentBlue, AccentGreen)
                                )
                            )
                    )
                }
                Spacer(modifier = Modifier.height(3.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = "Progression TP",
                        color = TextMuted,
                        fontSize = 9.5.sp
                    )
                    Text(
                        text = "${signal.progress}%",
                        color = TextMain,
                        fontSize = 9.5.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Footer button: Voir le graphique
            Button(
                onClick = onOpenChart,
                colors = ButtonDefaults.buttonColors(
                    containerColor = BgInset,
                    contentColor = TextMuted
                ),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor, RoundedCornerShape(8.dp))
                    .testTag("open_chart_${asset.symbol}")
            ) {
                Icon(
                    imageVector = Icons.Default.ShowChart,
                    contentDescription = null,
                    modifier = Modifier.size(15.dp),
                    tint = AccentBlue
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "Voir le graphique live",
                    fontSize = 11.5.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

@Composable
private fun StatusBadge(
    status: String,
    direction: SignalDirection
) {
    val (bgColor, textColor, text) = when (status) {
        "TP_HIT" -> Triple(AccentGreenSoft, AccentGreen, "TP TOUCHÉ")
        "SL_HIT" -> Triple(AccentRedSoft, AccentRed, "SL TOUCHÉ")
        "EXPIRED" -> Triple(BgInset, TextFaint, "EXPIRÉ")
        "STANDBY" -> Triple(BgInset, TextFaint, "STANDBY")
        else -> {
            when (direction) {
                SignalDirection.BUY -> Triple(AccentGreenSoft, AccentGreen, status.ifBlank { "BUY ACTIF" })
                SignalDirection.SELL -> Triple(AccentRedSoft, AccentRed, status.ifBlank { "SELL ACTIF" })
                SignalDirection.NONE -> Triple(BgInset, TextFaint, status)
            }
        }
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(bgColor)
            .border(1.dp, textColor.copy(alpha = 0.35f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(
            text = text,
            color = textColor,
            fontSize = 9.5.sp,
            fontWeight = FontWeight.ExtraBold,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun QualityChip(quality: String) {
    val (bg, color) = when (quality) {
        "A+" -> Pair(AccentPurpleSoft, AccentPurple)
        "A" -> Pair(AccentBlueSoft, AccentBlue)
        else -> Pair(BgInset, TextFaint)
    }
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(5.dp))
            .background(bg)
            .border(1.dp, color.copy(alpha = 0.4f), RoundedCornerShape(5.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = "GRADE $quality",
            color = color,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun GradeChip(grade: String) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(5.dp))
            .background(AccentGoldSoft)
            .border(1.dp, AccentGold.copy(alpha = 0.4f), RoundedCornerShape(5.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = grade,
            color = AccentGold,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun Chip(text: String) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(5.dp))
            .background(BgInset)
            .border(1.dp, BorderSoft, RoundedCornerShape(5.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = text,
            color = TextMuted,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun DataRow(
    label: String,
    value: String,
    valueColor: Color = TextMain
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            color = TextMuted,
            fontSize = 11.5.sp
        )
        Text(
            text = value,
            color = valueColor,
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold,
            fontFamily = FontFamily.Monospace
        )
    }
}

private fun formatNumber(valDouble: Double?, decimals: Int): String {
    if (valDouble == null) return "--"
    return String.format(java.util.Locale.US, "%.${decimals}f", valDouble)
}

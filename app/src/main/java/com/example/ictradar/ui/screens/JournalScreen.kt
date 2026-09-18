package com.example.ictradar.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.model.JournalTrade
import com.example.ictradar.data.model.SignalDirection
import com.example.ictradar.ui.PerformanceMetrics
import com.example.ictradar.ui.components.EquityCurveChart
import com.example.ictradar.ui.components.MetricCard
import com.example.ictradar.ui.components.WinRateGauge
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentGreenSoft
import com.example.ictradar.ui.theme.AccentPurple
import com.example.ictradar.ui.theme.AccentPurpleSoft
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.AccentRedSoft
import com.example.ictradar.ui.theme.BgBody
import com.example.ictradar.ui.theme.BgCard
import com.example.ictradar.ui.theme.BgElevated
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.BorderSoft
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun JournalScreen(
    trades: List<JournalTrade>,
    metrics: PerformanceMetrics,
    riskEur: Double,
    capitalEur: Double,
    onRiskChange: (Double) -> Unit,
    onCapitalChange: (Double) -> Unit,
    modifier: Modifier = Modifier
) {
    var riskInput by remember(riskEur) { mutableStateOf(riskEur.toInt().toString()) }
    var capitalInput by remember(capitalEur) { mutableStateOf(capitalEur.toInt().toString()) }

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(BgBody)
            .padding(horizontal = 14.dp),
        contentPadding = PaddingValues(top = 14.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Section: Config Risque & Portefeuille
        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp)
            ) {
                Text(
                    text = "GESTION DU RISQUE & CAPITAL",
                    color = TextMuted,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.6.sp
                )
                Spacer(modifier = Modifier.height(10.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    // Risk input
                    OutlinedTextField(
                        value = riskInput,
                        onValueChange = {
                            riskInput = it
                            it.toDoubleOrNull()?.let { v -> onRiskChange(v) }
                        },
                        label = { Text("Risque / trade (€)", fontSize = 11.sp) },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AccentBlue,
                            unfocusedBorderColor = BorderSoft,
                            focusedTextColor = TextMain,
                            unfocusedTextColor = TextMain,
                            focusedContainerColor = BgInset,
                            unfocusedContainerColor = BgInset
                        ),
                        singleLine = true,
                        modifier = Modifier
                            .weight(1f)
                            .testTag("risk_input")
                    )

                    // Portfolio capital input
                    OutlinedTextField(
                        value = capitalInput,
                        onValueChange = {
                            capitalInput = it
                            it.toDoubleOrNull()?.let { v -> onCapitalChange(v) }
                        },
                        label = { Text("Portefeuille (€)", fontSize = 11.sp) },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AccentBlue,
                            unfocusedBorderColor = BorderSoft,
                            focusedTextColor = TextMain,
                            unfocusedTextColor = TextMain,
                            focusedContainerColor = BgInset,
                            unfocusedContainerColor = BgInset
                        ),
                        singleLine = true,
                        modifier = Modifier
                            .weight(1f)
                            .testTag("capital_input")
                    )
                }
            }
        }

        // Section: Performance KPI Grid
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    MetricCard(
                        label = "Gagnés / Perdus",
                        value = "${metrics.wins} / ${metrics.losses}",
                        subValue = "${metrics.totalTrades} clôturé(s)",
                        valueColor = AccentGreen,
                        modifier = Modifier.weight(1f)
                    )
                    MetricCard(
                        label = "Profit Factor",
                        value = metrics.profitFactor?.let { if (it >= 90) "∞" else String.format(Locale.US, "%.2f", it) } ?: "--",
                        valueColor = AccentBlue,
                        modifier = Modifier.weight(1f)
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val rColor = if (metrics.totalR > 0) AccentGreen else if (metrics.totalR < 0) AccentRed else TextMain
                    val rSign = if (metrics.totalR >= 0) "+" else ""
                    MetricCard(
                        label = "R Total Cumulé",
                        value = "$rSign${String.format(Locale.US, "%.2f", metrics.totalR)}R",
                        valueColor = rColor,
                        modifier = Modifier.weight(1f)
                    )

                    val pnlColor = if (metrics.pnlEur > 0) AccentGreen else if (metrics.pnlEur < 0) AccentRed else TextMain
                    val pnlSign = if (metrics.pnlEur >= 0) "+" else ""
                    MetricCard(
                        label = "P&L Net Estimé",
                        value = "$pnlSign${String.format(Locale.US, "%,.2f", metrics.pnlEur)} €",
                        subValue = "Solde: ${String.format(Locale.US, "%,.2f", metrics.balanceEur)} €",
                        valueColor = pnlColor,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        // Section: Win Rate Gauge & Equity Curve
        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp)
            ) {
                Text(
                    text = "ANALYTIQUE & COURBE DE PERFORMANCE",
                    color = TextMuted,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.6.sp
                )
                Spacer(modifier = Modifier.height(14.dp))

                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    WinRateGauge(
                        winRatePct = metrics.winRatePct,
                        totalTrades = metrics.totalTrades
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))
                Text(
                    text = "ÉVOLUTION DU CAPITAL (EQUITY CURVE)",
                    color = TextFaint,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(6.dp))
                EquityCurveChart(
                    equityPoints = metrics.equityPoints,
                    initialCapital = capitalEur
                )
            }
        }

        // Section: Trade History Table
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "HISTORIQUE DES TRADES (JOURNAL)",
                    color = TextMuted,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "${trades.size} enregistrement(s)",
                    color = TextFaint,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }

        if (trades.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .background(BgCard)
                        .border(1.dp, BorderColor, RoundedCornerShape(10.dp))
                        .padding(32.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "En attente du premier signal clôturé…",
                        color = TextFaint,
                        fontSize = 12.sp
                    )
                }
            }
        } else {
            items(trades, key = { it.id }) { trade ->
                TradeHistoryCard(trade = trade)
            }
        }
    }
}

@Composable
private fun TradeHistoryCard(trade: JournalTrade) {
    val isWin = trade.rMultiple > 0
    val isLoss = trade.rMultiple < 0
    val resultColor = if (isWin) AccentGreen else if (isLoss) AccentRed else TextMuted
    val resultSign = if (trade.rMultiple >= 0) "+" else ""

    val timeStr = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date(trade.timestamp))

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(BgCard)
            .border(1.dp, BorderColor, RoundedCornerShape(10.dp))
            .padding(12.dp)
            .testTag("journal_trade_${trade.symbol}")
    ) {
        Column {
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
                        text = trade.symbol,
                        color = TextMain,
                        fontSize = 13.5.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = trade.direction.name,
                        color = if (trade.direction == SignalDirection.BUY) AccentGreen else AccentRed,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                    if (trade.quality != "--" && trade.quality.isNotBlank()) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .background(if (trade.quality == "A+") AccentPurpleSoft else AccentGreenSoft)
                                .padding(horizontal = 5.dp, vertical = 1.dp)
                        ) {
                            Text(
                                text = trade.quality,
                                color = if (trade.quality == "A+") AccentPurple else AccentGreen,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }
                }

                // Result R
                Text(
                    text = "$resultSign${String.format(Locale.US, "%.2f", trade.rMultiple)}R",
                    color = resultColor,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.ExtraBold,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = trade.setupType,
                    color = TextMuted,
                    fontSize = 11.sp
                )
                Text(
                    text = trade.session,
                    color = TextFaint,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Entrée: ${trade.entryPrice?.let { String.format(Locale.US, "%.2f", it) } ?: "--"}",
                    color = TextFaint,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = timeStr,
                    color = TextFaint,
                    fontSize = 9.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
    }
}

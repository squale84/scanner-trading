package com.example.ictradar.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material.icons.filled.TrackChanges
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.model.AssetCategory
import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.TradingAsset
import com.example.ictradar.ui.ScannerFilter
import com.example.ictradar.ui.components.AssetCard
import com.example.ictradar.ui.components.MetricCard
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.BgBody
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.BorderSoft
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted

@Composable
fun ScannerScreen(
    signals: Map<String, SignalData>,
    totalAlerts: Int,
    tpCount: Int,
    slCount: Int,
    riskEur: Double,
    activeFilter: ScannerFilter,
    onSelectFilter: (ScannerFilter) -> Unit,
    onResetAsset: (String) -> Unit,
    onOpenChart: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val totalClosed = tpCount + slCount
    val winRateStr = if (totalClosed > 0) "${(tpCount * 100) / totalClosed}%" else "--"
    val activeCount = signals.values.count { it.isActive }

    // Filter assets
    val filteredAssets = TradingAsset.ALL_ASSETS.filter { asset ->
        val sig = signals[asset.symbol]
        val isActive = sig?.isActive == true
        when (activeFilter) {
            ScannerFilter.ALL -> true
            ScannerFilter.ACTIVE -> isActive
            ScannerFilter.TRAD -> asset.category == AssetCategory.TRAD
            ScannerFilter.CRYPTO -> asset.category == AssetCategory.CRYPTO
        }
    }

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(BgBody)
            .padding(horizontal = 14.dp),
        contentPadding = PaddingValues(top = 14.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // KPI Metrics Row
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                MetricCard(
                    label = "Alertes",
                    value = "$totalAlerts",
                    icon = Icons.Default.NotificationsActive,
                    valueColor = AccentBlue,
                    modifier = Modifier.weight(1f)
                )
                MetricCard(
                    label = "Actives",
                    value = "$activeCount",
                    icon = Icons.Default.TrackChanges,
                    valueColor = AccentGreen,
                    modifier = Modifier.weight(1f)
                )
                MetricCard(
                    label = "Win Rate",
                    value = winRateStr,
                    icon = Icons.Default.BarChart,
                    valueColor = AccentGreen,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        // Filter chips row
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                FilterTab(
                    text = "TOUS",
                    count = TradingAsset.ALL_ASSETS.size,
                    isSelected = activeFilter == ScannerFilter.ALL,
                    onClick = { onSelectFilter(ScannerFilter.ALL) }
                )
                FilterTab(
                    text = "ACTIFS",
                    count = activeCount,
                    isSelected = activeFilter == ScannerFilter.ACTIVE,
                    onClick = { onSelectFilter(ScannerFilter.ACTIVE) }
                )
                FilterTab(
                    text = "TRADFI",
                    count = TradingAsset.ALL_ASSETS.count { it.category == AssetCategory.TRAD },
                    isSelected = activeFilter == ScannerFilter.TRAD,
                    onClick = { onSelectFilter(ScannerFilter.TRAD) }
                )
                FilterTab(
                    text = "CRYPTO",
                    count = TradingAsset.ALL_ASSETS.count { it.category == AssetCategory.CRYPTO },
                    isSelected = activeFilter == ScannerFilter.CRYPTO,
                    onClick = { onSelectFilter(ScannerFilter.CRYPTO) }
                )
            }
        }

        if (filteredAssets.isEmpty()) {
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 40.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Aucun actif correspondant au filtre.",
                        color = TextFaint,
                        fontSize = 13.sp
                    )
                }
            }
        } else {
            items(filteredAssets, key = { it.symbol }) { asset ->
                val sig = signals[asset.symbol] ?: SignalData(symbol = asset.symbol, currentPrice = asset.initialPrice)
                AssetCard(
                    asset = asset,
                    signal = sig,
                    riskEur = riskEur,
                    onReset = { onResetAsset(asset.symbol) },
                    onOpenChart = { onOpenChart(asset.symbol) }
                )
            }
        }
    }
}

@Composable
private fun FilterTab(
    text: String,
    count: Int,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val bg = if (isSelected) AccentBlue.copy(alpha = 0.16f) else BgInset
    val border = if (isSelected) AccentBlue else BorderSoft
    val textColor = if (isSelected) AccentBlue else TextMuted

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .border(1.dp, border, RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 6.dp)
            .testTag("filter_tab_$text")
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                text = text,
                color = textColor,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = " $count",
                color = if (isSelected) textColor else TextFaint,
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

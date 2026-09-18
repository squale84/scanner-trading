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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.model.EconomicEvent
import com.example.ictradar.ui.CalendarImpactFilter
import com.example.ictradar.ui.CalendarPeriod
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGold
import com.example.ictradar.ui.theme.AccentGoldSoft
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.AccentRedSoft
import com.example.ictradar.ui.theme.BgBody
import com.example.ictradar.ui.theme.BgCard
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
fun CalendarScreen(
    events: List<EconomicEvent>,
    isLoading: Boolean,
    period: CalendarPeriod,
    impact: CalendarImpactFilter,
    onSelectPeriod: (CalendarPeriod) -> Unit,
    onSelectImpact: (CalendarImpactFilter) -> Unit,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier
) {
    val filtered = events.filter { ev ->
        val matchesPeriod = when (period) {
            CalendarPeriod.TODAY -> ev.isToday()
            CalendarPeriod.WEEK -> true
        }
        val matchesImpact = when (impact) {
            CalendarImpactFilter.ALL -> true
            CalendarImpactFilter.HIGH -> ev.impact.equals("High", ignoreCase = true)
            CalendarImpactFilter.MEDIUM -> ev.impact.equals("Medium", ignoreCase = true)
        }
        matchesPeriod && matchesImpact
    }

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(BgBody)
            .padding(horizontal = 14.dp),
        contentPadding = PaddingValues(top = 14.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Header with Refresh & Timezone
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "📅 CALENDRIER ÉCONOMIQUE",
                        color = TextMain,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.ExtraBold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = "Flux ForexFactory • Fuseau horaire local",
                        color = TextMuted,
                        fontSize = 10.sp
                    )
                }

                IconButton(
                    onClick = onRefresh,
                    enabled = !isLoading,
                    modifier = Modifier
                        .size(34.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(BgInset)
                        .border(1.dp, BorderColor, RoundedCornerShape(8.dp))
                        .testTag("refresh_calendar_btn")
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(
                            color = AccentBlue,
                            strokeWidth = 2.dp,
                            modifier = Modifier.size(16.dp)
                        )
                    } else {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh",
                            tint = AccentBlue,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }
        }

        // Filters: Period and Impact
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                // Period Filters
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    PeriodButton(
                        text = "🎯 AUJOURD'HUI",
                        isSelected = period == CalendarPeriod.TODAY,
                        onClick = { onSelectPeriod(CalendarPeriod.TODAY) }
                    )
                    PeriodButton(
                        text = "SEMAINE",
                        isSelected = period == CalendarPeriod.WEEK,
                        onClick = { onSelectPeriod(CalendarPeriod.WEEK) }
                    )
                }

                // Impact Filters
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    ImpactButton(
                        text = "TOUS",
                        isSelected = impact == CalendarImpactFilter.ALL,
                        onClick = { onSelectImpact(CalendarImpactFilter.ALL) }
                    )
                    ImpactButton(
                        text = "HIGH",
                        isSelected = impact == CalendarImpactFilter.HIGH,
                        color = AccentRed,
                        onClick = { onSelectImpact(CalendarImpactFilter.HIGH) }
                    )
                    ImpactButton(
                        text = "MEDIUM",
                        isSelected = impact == CalendarImpactFilter.MEDIUM,
                        color = AccentGold,
                        onClick = { onSelectImpact(CalendarImpactFilter.MEDIUM) }
                    )
                }
            }
        }

        if (filtered.isEmpty()) {
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
                        text = if (isLoading) "Chargement du calendrier…" else "Aucun événement pour ce filtre.",
                        color = TextFaint,
                        fontSize = 12.sp
                    )
                }
            }
        } else {
            items(filtered) { event ->
                EconomicEventCard(event = event)
            }
        }
    }
}

@Composable
private fun PeriodButton(
    text: String,
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
            .padding(horizontal = 12.dp, vertical = 6.dp)
    ) {
        Text(
            text = text,
            color = textColor,
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun ImpactButton(
    text: String,
    isSelected: Boolean,
    color: androidx.compose.ui.graphics.Color = AccentBlue,
    onClick: () -> Unit
) {
    val bg = if (isSelected) color.copy(alpha = 0.16f) else BgInset
    val border = if (isSelected) color else BorderSoft
    val textColor = if (isSelected) color else TextMuted

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(bg)
            .border(1.dp, border, RoundedCornerShape(8.dp))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 5.dp)
    ) {
        Text(
            text = text,
            color = textColor,
            fontSize = 10.5.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun EconomicEventCard(event: EconomicEvent) {
    val ts = event.parsedTimestamp()
    val timeFormatted = if (ts > 0) {
        SimpleDateFormat("EEE dd/MM • HH:mm", Locale.getDefault()).format(Date(ts))
    } else event.date

    val minutesLeft = event.minutesUntil()
    val isImminent = minutesLeft in 0..60
    val isNow = minutesLeft in -15..15

    val cardBorder = when {
        isNow -> AccentRed
        isImminent -> AccentGold
        else -> BorderColor
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(10.dp))
            .background(BgCard)
            .border(1.dp, cardBorder, RoundedCornerShape(10.dp))
            .padding(12.dp)
            .testTag("economic_event_${event.title}")
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
                        text = event.country,
                        color = TextMain,
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 13.sp,
                        fontFamily = FontFamily.Monospace
                    )

                    ImpactBadge(impact = event.impact)

                    if (isNow) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .background(AccentRedSoft)
                                .padding(horizontal = 5.dp, vertical = 2.dp)
                        ) {
                            Text(
                                text = "EN COURS",
                                color = AccentRed,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.ExtraBold
                            )
                        }
                    } else if (isImminent) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .background(AccentGoldSoft)
                                .padding(horizontal = 5.dp, vertical = 2.dp)
                        ) {
                            Text(
                                text = "DANS ${minutesLeft}M",
                                color = AccentGold,
                                fontSize = 8.5.sp,
                                fontWeight = FontWeight.ExtraBold
                            )
                        }
                    }
                }

                Text(
                    text = timeFormatted,
                    color = TextMuted,
                    fontSize = 10.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = event.title,
                color = TextMain,
                fontSize = 12.5.sp,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(6.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "Prévision: ${event.forecast.ifBlank { "--" }}",
                    color = TextMuted,
                    fontSize = 10.5.sp,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "Précédent: ${event.previous.ifBlank { "--" }}",
                    color = TextFaint,
                    fontSize = 10.5.sp,
                    fontFamily = FontFamily.Monospace
                )
            }
        }
    }
}

@Composable
private fun ImpactBadge(impact: String) {
    val (bg, textColor) = when (impact.lowercase()) {
        "high" -> Pair(AccentRedSoft, AccentRed)
        "medium" -> Pair(AccentGoldSoft, AccentGold)
        else -> Pair(BgInset, TextFaint)
    }

    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(4.dp))
            .background(bg)
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = impact.uppercase(),
            color = textColor,
            fontSize = 8.5.sp,
            fontWeight = FontWeight.ExtraBold,
            letterSpacing = 0.4.sp
        )
    }
}

package com.example.ictradar.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.ui.theme.AccentGold
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted

@Composable
fun WinRateGauge(
    winRatePct: Int?,
    totalTrades: Int,
    modifier: Modifier = Modifier
) {
    val pct = winRatePct ?: 0
    val color = when {
        pct >= 60 -> AccentGreen
        pct >= 40 -> AccentGold
        else -> AccentRed
    }

    Box(
        modifier = modifier.size(170.dp, 105.dp),
        contentAlignment = Alignment.BottomCenter
    ) {
        Canvas(modifier = Modifier.matchParentSize()) {
            val strokeWidth = 14.dp.toPx()
            val diameter = size.width - strokeWidth
            val arcSize = Size(diameter, diameter)
            val topLeft = Offset(strokeWidth / 2, strokeWidth / 2)

            // Background arc (180 degrees from 180 to 0)
            drawArc(
                color = BorderColor,
                startAngle = 180f,
                sweepAngle = 180f,
                useCenter = false,
                topLeft = topLeft,
                size = arcSize,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )

            // Foreground arc
            if (winRatePct != null && pct > 0) {
                val sweep = (pct / 100f) * 180f
                drawArc(
                    color = color,
                    startAngle = 180f,
                    sweepAngle = sweep,
                    useCenter = false,
                    topLeft = topLeft,
                    size = arcSize,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )
            }
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.align(Alignment.Center)
        ) {
            Text(
                text = if (winRatePct == null) "--" else "$pct%",
                color = TextMain,
                fontSize = 24.sp,
                fontWeight = FontWeight.ExtraBold,
                fontFamily = FontFamily.Monospace
            )
            Text(
                text = "$totalTrades trade(s)",
                color = TextMuted,
                fontSize = 9.5.sp,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}

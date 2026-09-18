package com.example.ictradar.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.BgCard
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.BorderSoft
import com.example.ictradar.ui.theme.TextFaint

@Composable
fun EquityCurveChart(
    equityPoints: List<Double>,
    initialCapital: Double,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(160.dp)
            .clip(RoundedCornerShape(10.dp))
            .background(BgCard)
            .border(1.dp, BorderColor, RoundedCornerShape(10.dp))
            .padding(8.dp),
        contentAlignment = Alignment.Center
    ) {
        if (equityPoints.isEmpty() || equityPoints.size == 1) {
            Text(
                text = "Pas encore de trade clôturé",
                color = TextFaint,
                fontSize = 12.sp
            )
            return
        }

        Canvas(modifier = Modifier.fillMaxSize().padding(horizontal = 8.dp, vertical = 6.dp)) {
            val minVal = equityPoints.minOrNull() ?: initialCapital
            val maxVal = equityPoints.maxOrNull() ?: initialCapital
            val range = if (maxVal - minVal == 0.0) 1.0 else (maxVal - minVal)

            val width = size.width
            val height = size.height

            val stepX = width / (equityPoints.size - 1)

            val points = equityPoints.mapIndexed { index, v ->
                val x = index * stepX
                val y = height - (((v - minVal) / range) * (height * 0.82f) + (height * 0.09f)).toFloat()
                Offset(x, y)
            }

            // Draw baseline for initialCapital
            val baseLineY = height - (((initialCapital - minVal) / range) * (height * 0.82f) + (height * 0.09f)).toFloat()
            drawLine(
                color = BorderSoft,
                start = Offset(0f, baseLineY),
                end = Offset(width, baseLineY),
                strokeWidth = 1.5f,
                pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f), 0f)
            )

            val isProfitable = (equityPoints.lastOrNull() ?: initialCapital) >= initialCapital
            val strokeColor = if (isProfitable) AccentGreen else AccentRed

            val strokePath = Path().apply {
                moveTo(points.first().x, points.first().y)
                for (i in 1 until points.size) {
                    lineTo(points[i].x, points[i].y)
                }
            }

            val fillPath = Path().apply {
                addPath(strokePath)
                lineTo(points.last().x, height)
                lineTo(points.first().x, height)
                close()
            }

            // Draw gradient area
            drawPath(
                path = fillPath,
                brush = Brush.verticalGradient(
                    colors = listOf(strokeColor.copy(alpha = 0.35f), Color.Transparent),
                    startY = 0f,
                    endY = height
                )
            )

            // Draw curve line
            drawPath(
                path = strokePath,
                color = strokeColor,
                style = Stroke(
                    width = 2.5.dp.toPx(),
                    cap = StrokeCap.Round,
                    join = StrokeJoin.Round
                )
            )

            // Draw dot on last point
            drawCircle(
                color = strokeColor,
                radius = 4.dp.toPx(),
                center = points.last()
            )
        }
    }
}

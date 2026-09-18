package com.example.ictradar.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.unit.dp
import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.TradingAsset
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderSoft
import kotlin.random.Random

data class Candle(
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double
)

@Composable
fun CandleStickChart(
    asset: TradingAsset,
    signal: SignalData,
    modifier: Modifier = Modifier
) {
    val currentPrice = signal.currentPrice ?: asset.initialPrice

    // Generate stable synthetic candles around current price
    val candles = remember(asset.symbol) {
        val list = mutableListOf<Candle>()
        var base = currentPrice * 0.992
        val step = currentPrice * 0.003
        for (i in 0 until 28) {
            val isBull = Random.nextDouble() > 0.48
            val open = base
            val delta = (Random.nextDouble() * 0.8 + 0.2) * step
            val close = if (isBull) open + delta else open - delta
            val high = maxOf(open, close) + Random.nextDouble() * step * 0.5
            val low = minOf(open, close) - Random.nextDouble() * step * 0.5
            list.add(Candle(open, high, low, close))
            base = close
        }
        list
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(240.dp)
            .clip(RoundedCornerShape(8.dp))
            .background(BgInset)
            .padding(4.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize().padding(end = 46.dp, top = 12.dp, bottom = 12.dp, start = 8.dp)) {
            val allHighs = candles.map { it.high }.toMutableList()
            val allLows = candles.map { it.low }.toMutableList()

            signal.tpPrice?.let { allHighs.add(it) }
            signal.slPrice?.let { allLows.add(it) }
            signal.entryPrice?.let { allHighs.add(it); allLows.add(it) }

            val minVal = allLows.minOrNull() ?: currentPrice * 0.98
            val maxVal = allHighs.maxOrNull() ?: currentPrice * 1.02
            val range = if (maxVal - minVal <= 0.0) 1.0 else (maxVal - minVal)

            val width = size.width
            val height = size.height

            val candleWidth = width / candles.size
            val barWidth = candleWidth * 0.65f

            val toY = { price: Double ->
                height - (((price - minVal) / range) * height).toFloat()
            }

            // Grid lines
            for (i in 1..4) {
                val gridY = height * (i / 5f)
                drawLine(
                    color = BorderSoft,
                    start = Offset(0f, gridY),
                    end = Offset(width + 46.dp.toPx(), gridY),
                    strokeWidth = 1f
                )
            }

            // Draw candles
            candles.forEachIndexed { i, c ->
                val centerX = i * candleWidth + candleWidth / 2
                val openY = toY(c.open)
                val closeY = toY(c.close)
                val highY = toY(c.high)
                val lowY = toY(c.low)

                val isGreen = c.close >= c.open
                val candleColor = if (isGreen) AccentGreen else AccentRed

                // Wick
                drawLine(
                    color = candleColor,
                    start = Offset(centerX, highY),
                    end = Offset(centerX, lowY),
                    strokeWidth = 1.5.dp.toPx()
                )

                // Body
                val bodyTop = minOf(openY, closeY)
                val bodyHeight = maxOf(Math.abs(closeY - openY), 2f)
                drawRect(
                    color = candleColor,
                    topLeft = Offset(centerX - barWidth / 2, bodyTop),
                    size = Size(barWidth, bodyHeight)
                )
            }

            // Draw ICT Setup lines if available
            val dashEffect = PathEffect.dashPathEffect(floatArrayOf(12f, 8f), 0f)

            // TP Level
            signal.tpPrice?.let { tp ->
                val tpY = toY(tp)
                drawLine(
                    color = AccentGreen,
                    start = Offset(0f, tpY),
                    end = Offset(width + 44.dp.toPx(), tpY),
                    strokeWidth = 2.dp.toPx(),
                    pathEffect = dashEffect
                )
                drawPriceLabel("TP", tp, tpY, AccentGreen, asset.decimals)
            }

            // Entry Level
            signal.entryPrice?.let { ep ->
                val epY = toY(ep)
                drawLine(
                    color = AccentBlue,
                    start = Offset(0f, epY),
                    end = Offset(width + 44.dp.toPx(), epY),
                    strokeWidth = 2.dp.toPx(),
                    pathEffect = dashEffect
                )
                drawPriceLabel("ENTRY", ep, epY, AccentBlue, asset.decimals)
            }

            // SL Level
            signal.slPrice?.let { sl ->
                val slY = toY(sl)
                drawLine(
                    color = AccentRed,
                    start = Offset(0f, slY),
                    end = Offset(width + 44.dp.toPx(), slY),
                    strokeWidth = 2.dp.toPx(),
                    pathEffect = dashEffect
                )
                drawPriceLabel("SL", sl, slY, AccentRed, asset.decimals)
            }

            // Current price line
            val curY = toY(currentPrice)
            drawLine(
                color = Color.White.copy(alpha = 0.5f),
                start = Offset(0f, curY),
                end = Offset(width + 44.dp.toPx(), curY),
                strokeWidth = 1.dp.toPx()
            )
            drawPriceLabel("PRICE", currentPrice, curY, Color.White, asset.decimals)
        }
    }
}

private fun DrawScope.drawPriceLabel(
    tag: String,
    price: Double,
    y: Float,
    color: Color,
    decimals: Int
) {
    val text = "$tag ${String.format(java.util.Locale.US, "%.${decimals}f", price)}"
    val paint = android.graphics.Paint().apply {
        this.color = color.hashCode()
        textSize = 24f
        isAntiAlias = true
        typeface = android.graphics.Typeface.MONOSPACE
        isFakeBoldText = true
    }

    drawContext.canvas.nativeCanvas.drawText(
        text,
        size.width + 2.dp.toPx(),
        y + 8f,
        paint
    )
}

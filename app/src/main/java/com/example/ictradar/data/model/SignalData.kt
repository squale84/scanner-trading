package com.example.ictradar.data.model

import kotlinx.serialization.Serializable

@Serializable
enum class SignalDirection {
    BUY,
    SELL,
    NONE
}

@Serializable
data class SignalData(
    val symbol: String,
    val status: String = "STANDBY", // "STANDBY", "SSL SWEEP", "BSL SWEEP", "RETEST", "TP_HIT", "SL_HIT", "EXPIRED"
    val direction: SignalDirection = SignalDirection.NONE,
    val quality: String = "--", // "A+", "A"
    val grade: String = "--", // "★★★★★", "★★★★☆"
    val rr: String = "0.0", // "2.0"
    val entryPrice: Double? = null,
    val slPrice: Double? = null,
    val tpPrice: Double? = null,
    val currentPrice: Double? = null,
    val progress: Int = 0, // 0..100%
    val timestamp: Long = System.currentTimeMillis()
) {
    val isActive: Boolean
        get() = direction != SignalDirection.NONE &&
                status != "STANDBY" &&
                status != "TP_HIT" &&
                status != "SL_HIT" &&
                status != "EXPIRED"

    val isExit: Boolean
        get() = status == "TP_HIT" || status == "SL_HIT" || status == "EXPIRED"

    fun calculateProgress(curPrice: Double? = currentPrice): Int {
        if (entryPrice == null || tpPrice == null || curPrice == null) return 0
        if (isExit) {
            return if (status == "TP_HIT") 100 else 0
        }
        return when (direction) {
            SignalDirection.BUY -> {
                if (tpPrice > entryPrice) {
                    val p = ((curPrice - entryPrice) / (tpPrice - entryPrice) * 100).toInt()
                    p.coerceIn(0, 100)
                } else 0
            }
            SignalDirection.SELL -> {
                if (entryPrice > tpPrice) {
                    val p = ((entryPrice - curPrice) / (entryPrice - tpPrice) * 100).toInt()
                    p.coerceIn(0, 100)
                } else 0
            }
            SignalDirection.NONE -> 0
        }
    }

    fun suggestedSize(riskEur: Double): Double? {
        if (entryPrice == null || slPrice == null) return null
        val dist = kotlin.math.abs(entryPrice - slPrice)
        if (dist <= 0.0) return null
        return riskEur / dist
    }

    fun setupIctLabel(): String {
        return when (status) {
            "SSL SWEEP" -> "🐢 Turtle Soup (SSL)"
            "BSL SWEEP" -> "🐢 Turtle Soup (BSL)"
            "RETEST" -> "🔄 Retest FVG/OB"
            "TP_HIT" -> "🎯 TP Touché"
            "SL_HIT" -> "🛑 SL Touché"
            "EXPIRED" -> "⏱ Expiré"
            "STANDBY" -> "⏳ Standby"
            else -> status
        }
    }
}

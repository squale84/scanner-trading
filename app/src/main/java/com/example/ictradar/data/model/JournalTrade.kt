package com.example.ictradar.data.model

data class JournalTrade(
    val id: String = java.util.UUID.randomUUID().toString(),
    val timestamp: Long = System.currentTimeMillis(),
    val symbol: String,
    val direction: SignalDirection,
    val setupType: String,
    val session: String,
    val quality: String,
    val rr: String,
    val entryPrice: Double?,
    val exitPrice: Double?,
    val rMultiple: Double, // +2.0R, -1.0R, etc.
    val status: String // "TP_HIT", "SL_HIT", "EXPIRED"
)

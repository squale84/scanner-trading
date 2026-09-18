package com.example.ictradar.data.model

import kotlinx.serialization.Serializable

@Serializable
data class EconomicEvent(
    val title: String = "",
    val country: String = "",
    val date: String = "", // ISO string from FairEconomy: "2026-09-18T08:30:00-04:00"
    val impact: String = "Low", // "High", "Medium", "Low", "Holiday"
    val forecast: String = "--",
    val previous: String = "--"
) {
    fun parsedTimestamp(): Long {
        return try {
            java.time.OffsetDateTime.parse(date).toInstant().toEpochMilli()
        } catch (e: Exception) {
            try {
                java.time.Instant.parse(date).toEpochMilli()
            } catch (e2: Exception) {
                0L
            }
        }
    }

    fun isToday(): Boolean {
        val ts = parsedTimestamp()
        if (ts == 0L) return false
        val zone = java.time.ZoneId.systemDefault()
        val eventDate = java.time.Instant.ofEpochMilli(ts).atZone(zone).toLocalDate()
        val today = java.time.LocalDate.now(zone)
        return eventDate.isEqual(today)
    }

    fun minutesUntil(): Long {
        val ts = parsedTimestamp()
        if (ts == 0L) return 999999L
        return (ts - System.currentTimeMillis()) / 60000
    }
}

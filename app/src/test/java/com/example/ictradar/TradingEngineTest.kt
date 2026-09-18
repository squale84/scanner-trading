package com.example.ictradar

import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.SignalDirection
import com.example.ictradar.data.model.TradingAsset
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TradingEngineTest {

    @Test
    fun testAssetPresetList() {
        val assets = TradingAsset.ALL_ASSETS
        assertTrue(assets.isNotEmpty())
        assertTrue(assets.any { it.symbol == "GOLD" })
        assertTrue(assets.any { it.symbol == "BTCUSD" })
    }

    @Test
    fun testSignalProgressAndSizing() {
        val signal = SignalData(
            symbol = "GOLD",
            status = "SSL SWEEP",
            direction = SignalDirection.BUY,
            entryPrice = 2580.0,
            slPrice = 2570.0,
            tpPrice = 2600.0,
            currentPrice = 2590.0,
            rr = "2.0"
        )

        val progress = signal.calculateProgress()
        assertEquals(50, progress)

        val suggestedSize = signal.suggestedSize(riskEur = 100.0)
        assertNotNull(suggestedSize)
        assertEquals(10.0, suggestedSize!!, 0.001)
    }

    @Test
    fun testSignalExitCalculation() {
        val tpSignal = SignalData(
            symbol = "BTCUSD",
            status = "TP_HIT",
            direction = SignalDirection.NONE
        )
        assertTrue(tpSignal.isExit)
        assertEquals(100, tpSignal.calculateProgress())

        val slSignal = SignalData(
            symbol = "BTCUSD",
            status = "SL_HIT",
            direction = SignalDirection.NONE
        )
        assertTrue(slSignal.isExit)
        assertEquals(0, slSignal.calculateProgress())
    }
}

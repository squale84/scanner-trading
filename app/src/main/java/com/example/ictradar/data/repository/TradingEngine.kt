package com.example.ictradar.data.repository

import com.example.ictradar.data.model.AssetCategory
import com.example.ictradar.data.model.JournalTrade
import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.SignalDirection
import com.example.ictradar.data.model.TradingAsset
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.time.ZoneId
import java.time.ZonedDateTime
import java.util.concurrent.TimeUnit
import kotlin.random.Random

data class KillzoneStatus(
    val utcTime: String,
    val nyTime: String,
    val isLondonActive: Boolean,
    val isNyAmActive: Boolean
)

sealed class EngineAlert {
    data class NewSignal(val signal: SignalData) : EngineAlert()
    data class ExitHit(val signal: SignalData, val isTp: Boolean, val rMultiple: Double?) : EngineAlert()
}

class TradingEngine(private val scope: CoroutineScope) {

    private val _signals = MutableStateFlow<Map<String, SignalData>>(emptyMap())
    val signals: StateFlow<Map<String, SignalData>> = _signals.asStateFlow()

    private val _journalTrades = MutableStateFlow<List<JournalTrade>>(emptyList())
    val journalTrades: StateFlow<List<JournalTrade>> = _journalTrades.asStateFlow()

    private val _killzones = MutableStateFlow(calculateKillzones())
    val killzones: StateFlow<KillzoneStatus> = _killzones.asStateFlow()

    private val _alerts = MutableSharedFlow<EngineAlert>(extraBufferCapacity = 64)
    val alerts: SharedFlow<EngineAlert> = _alerts.asSharedFlow()

    private val _totalAlerts = MutableStateFlow(0)
    val totalAlerts: StateFlow<Int> = _totalAlerts.asStateFlow()

    private val _tpCount = MutableStateFlow(0)
    val tpCount: StateFlow<Int> = _tpCount.asStateFlow()

    private val _slCount = MutableStateFlow(0)
    val slCount: StateFlow<Int> = _slCount.asStateFlow()

    private val _riskEur = MutableStateFlow(100.0)
    val riskEur: StateFlow<Double> = _riskEur.asStateFlow()

    private val _capitalEur = MutableStateFlow(10000.0)
    val capitalEur: StateFlow<Double> = _capitalEur.asStateFlow()

    private val _isServerConnected = MutableStateFlow(false)
    val isServerConnected: StateFlow<Boolean> = _isServerConnected.asStateFlow()

    private val _serverUrl = MutableStateFlow("ws://10.0.2.2:8000/ws")
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    private val lastSignalData = mutableMapOf<String, SignalData>()
    private val lastSignalSession = mutableMapOf<String, String>()

    private var activeWebSocket: WebSocket? = null
    private var tickerJob: Job? = null
    private var clockJob: Job? = null

    init {
        // Initialize all assets with STANDBY status
        val initialMap = mutableMapOf<String, SignalData>()
        TradingAsset.ALL_ASSETS.forEach { asset ->
            initialMap[asset.symbol] = SignalData(
                symbol = asset.symbol,
                status = "STANDBY",
                direction = SignalDirection.NONE,
                currentPrice = asset.initialPrice
            )
        }
        _signals.value = initialMap

        // Start clock job
        clockJob = scope.launch {
            while (isActive) {
                _killzones.value = calculateKillzones()
                delay(1000)
            }
        }

        // Start market price live movement engine
        tickerJob = scope.launch {
            startPriceSimulation()
        }

        // Add 2 initial educational trades to journal for a rich initial institutional experience
        seedInitialTrades()
    }

    private fun seedInitialTrades() {
        val t1 = JournalTrade(
            symbol = "GOLD",
            direction = SignalDirection.BUY,
            setupType = "🐢 Turtle Soup (SSL)",
            session = "🇬🇧 Londres",
            quality = "A+",
            rr = "2.0",
            entryPrice = 2570.20,
            exitPrice = 2590.20,
            rMultiple = 2.0,
            status = "TP_HIT"
        )
        val t2 = JournalTrade(
            symbol = "BTCUSD",
            direction = SignalDirection.BUY,
            setupType = "🔄 Retest FVG/OB",
            session = "🇺🇸 NY AM",
            quality = "A",
            rr = "2.5",
            entryPrice = 62400.0,
            exitPrice = 64900.0,
            rMultiple = 2.5,
            status = "TP_HIT"
        )
        _journalTrades.value = listOf(t2, t1)
        _tpCount.value = 2
        _totalAlerts.value = 2
    }

    fun setRiskEur(eur: Double) {
        if (eur > 0) _riskEur.value = eur
    }

    fun setCapitalEur(eur: Double) {
        if (eur > 0) _capitalEur.value = eur
    }

    fun setServerUrl(url: String) {
        _serverUrl.value = url
    }

    fun resetAsset(symbol: String) {
        val current = _signals.value[symbol] ?: return
        val updated = current.copy(
            status = "STANDBY",
            direction = SignalDirection.NONE,
            entryPrice = null,
            slPrice = null,
            tpPrice = null,
            progress = 0,
            quality = "--",
            grade = "--",
            rr = "0.0"
        )
        _signals.value = _signals.value.toMutableMap().apply { put(symbol, updated) }
    }

    fun processSignalPayload(jsonStr: String) {
        try {
            val obj = JSONObject(jsonStr)
            val sym = obj.optString("symbol", "").uppercase()
            if (sym.isEmpty()) return

            val status = obj.optString("status", "STANDBY")
            val dirStr = obj.optString("direction", "NONE").uppercase()
            val direction = when (dirStr) {
                "BUY" -> SignalDirection.BUY
                "SELL" -> SignalDirection.SELL
                else -> SignalDirection.NONE
            }
            val quality = obj.optString("quality", "--")
            val grade = obj.optString("grade", "--")
            val rr = obj.optString("rr", "0.0")

            val ep = obj.optDouble("entry_price", Double.NaN).let { if (it.isNaN() || it <= 0.0) null else it }
            val slp = obj.optDouble("sl_price", Double.NaN).let { if (it.isNaN() || it <= 0.0) null else it }
            val tpp = obj.optDouble("tp_price", Double.NaN).let { if (it.isNaN() || it <= 0.0) null else it }
            val cp = obj.optDouble("current_price", Double.NaN).let { if (it.isNaN() || it <= 0.0) null else it }

            val sig = SignalData(
                symbol = sym,
                status = status,
                direction = direction,
                quality = quality,
                grade = grade,
                rr = rr,
                entryPrice = ep,
                slPrice = slp,
                tpPrice = tpp,
                currentPrice = cp ?: _signals.value[sym]?.currentPrice,
                progress = 0
            )
            val computed = sig.copy(progress = sig.calculateProgress())
            handleSignal(computed)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun handleSignal(signal: SignalData) {
        val sym = signal.symbol
        val isExit = signal.status == "TP_HIT" || signal.status == "SL_HIT" || signal.status == "EXPIRED"

        val updatedMap = _signals.value.toMutableMap()

        if (signal.status == "STANDBY") {
            val cur = updatedMap[sym] ?: signal
            updatedMap[sym] = cur.copy(
                status = "STANDBY",
                direction = SignalDirection.NONE,
                entryPrice = null,
                slPrice = null,
                tpPrice = null,
                progress = 0
            )
            _signals.value = updatedMap
            return
        }

        if (isExit) {
            val entryData = lastSignalData[sym]
            val sessionAtEntry = lastSignalSession[sym] ?: currentSessionLabel()
            var rMultiple: Double? = null

            if (signal.status == "TP_HIT") {
                rMultiple = entryData?.rr?.toDoubleOrNull() ?: 2.0
                _tpCount.value += 1
            } else if (signal.status == "SL_HIT") {
                rMultiple = -1.0
                _slCount.value += 1
            } else if (signal.status == "EXPIRED" && entryData != null) {
                val ep = entryData.entryPrice
                val slp = entryData.slPrice
                val xp = signal.currentPrice ?: entryData.currentPrice
                if (ep != null && slp != null && xp != null) {
                    val risk = kotlin.math.abs(ep - slp)
                    if (risk > 0.0) {
                        rMultiple = if (entryData.direction == SignalDirection.BUY) (xp - ep) / risk else (ep - xp) / risk
                    }
                }
            }

            if (rMultiple != null && entryData != null) {
                val trade = JournalTrade(
                    symbol = sym,
                    direction = entryData.direction,
                    setupType = entryData.setupIctLabel(),
                    session = sessionAtEntry,
                    quality = entryData.quality,
                    rr = entryData.rr,
                    entryPrice = entryData.entryPrice,
                    exitPrice = signal.currentPrice ?: (if (signal.status == "TP_HIT") entryData.tpPrice else entryData.slPrice),
                    rMultiple = rMultiple,
                    status = signal.status
                )
                _journalTrades.value = listOf(trade) + _journalTrades.value
            }

            val cur = updatedMap[sym] ?: signal
            updatedMap[sym] = cur.copy(
                status = signal.status,
                direction = SignalDirection.NONE,
                progress = if (signal.status == "TP_HIT") 100 else 0,
                currentPrice = signal.currentPrice ?: cur.currentPrice
            )
            _signals.value = updatedMap

            _alerts.tryEmit(EngineAlert.ExitHit(signal, signal.status == "TP_HIT", rMultiple))
            return
        }

        // New active entry signal
        if (signal.direction != SignalDirection.NONE) {
            lastSignalData[sym] = signal
            lastSignalSession[sym] = currentSessionLabel()

            updatedMap[sym] = signal.copy(progress = signal.calculateProgress())
            _signals.value = updatedMap
            _totalAlerts.value += 1

            _alerts.tryEmit(EngineAlert.NewSignal(signal))
        }
    }

    fun triggerSimulatedSignal() {
        val pool = listOf("GOLD", "US100", "BTCUSD", "ETHUSD", "EURUSD", "SOLUSD")
        val sym = pool.random()
        val isBuy = Random.nextBoolean()
        val dir = if (isBuy) SignalDirection.BUY else SignalDirection.SELL
        val curPrice = _signals.value[sym]?.currentPrice ?: 100.0

        val offset = when (sym) {
            "GOLD" -> 12.0
            "BTCUSD" -> 850.0
            "US100" -> 120.0
            "ETHUSD" -> 60.0
            "EURUSD" -> 0.0035
            "SOLUSD" -> 3.5
            else -> 10.0
        }

        val entry = curPrice
        val sl = if (isBuy) entry - offset else entry + offset
        val tp = if (isBuy) entry + (offset * 2.0) else entry - (offset * 2.0)
        val quality = if (Random.nextBoolean()) "A+" else "A"
        val grade = if (quality == "A+") "★★★★★" else "★★★★☆"
        val setupType = listOf("SSL SWEEP", "BSL SWEEP", "RETEST").random()

        val signal = SignalData(
            symbol = sym,
            status = setupType,
            direction = dir,
            quality = quality,
            grade = grade,
            rr = "2.0",
            entryPrice = entry,
            slPrice = sl,
            tpPrice = tp,
            currentPrice = entry,
            progress = 0
        )
        handleSignal(signal)

        // Schedule realistic exit after short delay for full loop simulation
        scope.launch {
            delay(12000)
            val curSig = _signals.value[sym]
            if (curSig != null && curSig.isActive) {
                val isWin = Random.nextDouble() > 0.35 // 65% win rate institutional setup
                val exitSig = SignalData(
                    symbol = sym,
                    status = if (isWin) "TP_HIT" else "SL_HIT",
                    direction = SignalDirection.NONE,
                    currentPrice = if (isWin) tp else sl
                )
                handleSignal(exitSig)
            }
        }
    }

    private suspend fun startPriceSimulation() {
        while (scope.isActive) {
            delay(2500)
            val updated = _signals.value.toMutableMap()
            updated.forEach { (sym, sig) ->
                val base = sig.currentPrice ?: 100.0
                val deltaPercent = (Random.nextDouble() - 0.5) * 0.0016
                val newPrice = (base * (1.0 + deltaPercent)).let {
                    val asset = TradingAsset.ALL_ASSETS.find { a -> a.symbol == sym }
                    val d = asset?.decimals ?: 2
                    val factor = Math.pow(10.0, d.toDouble())
                    Math.round(it * factor) / factor
                }

                val newProgress = if (sig.isActive) sig.calculateProgress(newPrice) else sig.progress

                // Auto TP/SL hit check during active setup
                if (sig.isActive && sig.entryPrice != null && sig.slPrice != null && sig.tpPrice != null) {
                    var exitStatus: String? = null
                    if (sig.direction == SignalDirection.BUY) {
                        if (newPrice >= sig.tpPrice) exitStatus = "TP_HIT"
                        else if (newPrice <= sig.slPrice) exitStatus = "SL_HIT"
                    } else if (sig.direction == SignalDirection.SELL) {
                        if (newPrice <= sig.tpPrice) exitStatus = "TP_HIT"
                        else if (newPrice >= sig.slPrice) exitStatus = "SL_HIT"
                    }

                    if (exitStatus != null) {
                        scope.launch {
                            handleSignal(SignalData(symbol = sym, status = exitStatus, currentPrice = newPrice))
                        }
                    }
                }

                updated[sym] = sig.copy(currentPrice = newPrice, progress = newProgress)
            }
            _signals.value = updated
        }
    }

    fun connectWebSocket() {
        disconnectWebSocket()
        val client = OkHttpClient.Builder()
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .build()

        val request = Request.Builder()
            .url(_serverUrl.value)
            .build()

        activeWebSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _isServerConnected.value = true
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                scope.launch(Dispatchers.Main) {
                    processSignalPayload(text)
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _isServerConnected.value = false
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _isServerConnected.value = false
            }
        })
    }

    fun disconnectWebSocket() {
        activeWebSocket?.close(1000, "User disconnected")
        activeWebSocket = null
        _isServerConnected.value = false
    }

    private fun calculateKillzones(): KillzoneStatus {
        val nowUtc = ZonedDateTime.now(ZoneId.of("UTC"))
        val nowNy = ZonedDateTime.now(ZoneId.of("America/New_York"))

        val nyHour = nowNy.hour
        val nyMin = nowNy.minute
        val nyDecimal = nyHour + (nyMin / 60.0)

        // London Killzone: 02:00 - 05:00 NY time
        val isLondon = nyDecimal in 2.0..5.0
        // NY AM Killzone: 08:30 - 11:00 NY time
        val isNyAm = nyDecimal in 8.5..11.0

        val utcStr = String.format("%02d:%02d:%02d UTC", nowUtc.hour, nowUtc.minute, nowUtc.second)
        val nyStr = String.format("%02d:%02d NY", nowNy.hour, nowNy.minute)

        return KillzoneStatus(
            utcTime = utcStr,
            nyTime = nyStr,
            isLondonActive = isLondon,
            isNyAmActive = isNyAm
        )
    }

    fun currentSessionLabel(): String {
        val kz = _killzones.value
        return if (kz.isLondonActive) "🇬🇧 Londres"
        else if (kz.isNyAmActive) "🇺🇸 NY AM"
        else "⏱ Hors killzone"
    }
}

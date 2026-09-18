package com.example.ictradar.ui

import android.app.Application
import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.ictradar.data.model.AssetCategory
import com.example.ictradar.data.model.EconomicEvent
import com.example.ictradar.data.model.JournalTrade
import com.example.ictradar.data.model.SignalData
import com.example.ictradar.data.model.TradingAsset
import com.example.ictradar.data.repository.CalendarRepository
import com.example.ictradar.data.repository.EngineAlert
import com.example.ictradar.data.repository.KillzoneStatus
import com.example.ictradar.data.repository.TradingEngine
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

enum class ScannerFilter {
    ALL,
    ACTIVE,
    TRAD,
    CRYPTO
}

enum class CalendarPeriod {
    TODAY,
    WEEK
}

enum class CalendarImpactFilter {
    ALL,
    HIGH,
    MEDIUM
}

data class PerformanceMetrics(
    val totalTrades: Int = 0,
    val wins: Int = 0,
    val losses: Int = 0,
    val winRatePct: Int? = null,
    val totalR: Double = 0.0,
    val profitFactor: Double? = null,
    val pnlEur: Double = 0.0,
    val balanceEur: Double = 10000.0,
    val equityPoints: List<Double> = emptyList()
)

data class ToastAlert(
    val id: String = java.util.UUID.randomUUID().toString(),
    val symbol: String,
    val title: String,
    val message: String,
    val isWin: Boolean? = null
)

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val tradingEngine = TradingEngine(viewModelScope)
    private val calendarRepo = CalendarRepository()

    val signals: StateFlow<Map<String, SignalData>> = tradingEngine.signals
    val journalTrades: StateFlow<List<JournalTrade>> = tradingEngine.journalTrades
    val killzones: StateFlow<KillzoneStatus> = tradingEngine.killzones

    val totalAlerts: StateFlow<Int> = tradingEngine.totalAlerts
    val tpCount: StateFlow<Int> = tradingEngine.tpCount
    val slCount: StateFlow<Int> = tradingEngine.slCount
    val riskEur: StateFlow<Double> = tradingEngine.riskEur
    val capitalEur: StateFlow<Double> = tradingEngine.capitalEur
    val isServerConnected: StateFlow<Boolean> = tradingEngine.isServerConnected
    val serverUrl: StateFlow<String> = tradingEngine.serverUrl

    // Filters
    private val _scannerFilter = MutableStateFlow(ScannerFilter.ALL)
    val scannerFilter: StateFlow<ScannerFilter> = _scannerFilter.asStateFlow()

    private val _calendarPeriod = MutableStateFlow(CalendarPeriod.TODAY)
    val calendarPeriod: StateFlow<CalendarPeriod> = _calendarPeriod.asStateFlow()

    private val _calendarImpact = MutableStateFlow(CalendarImpactFilter.ALL)
    val calendarImpact: StateFlow<CalendarImpactFilter> = _calendarImpact.asStateFlow()

    // Calendar data
    private val _calendarEvents = MutableStateFlow<List<EconomicEvent>>(emptyList())
    val calendarEvents: StateFlow<List<EconomicEvent>> = _calendarEvents.asStateFlow()

    private val _isCalendarLoading = MutableStateFlow(false)
    val isCalendarLoading: StateFlow<Boolean> = _isCalendarLoading.asStateFlow()

    // Detail sheet
    private val _selectedAssetSymbol = MutableStateFlow<String?>(null)
    val selectedAssetSymbol: StateFlow<String?> = _selectedAssetSymbol.asStateFlow()

    // Settings
    private val _audioEnabled = MutableStateFlow(true)
    val audioEnabled: StateFlow<Boolean> = _audioEnabled.asStateFlow()

    private val _vibrationEnabled = MutableStateFlow(true)
    val vibrationEnabled: StateFlow<Boolean> = _vibrationEnabled.asStateFlow()

    // Notifications
    private val _toastEvents = MutableSharedFlow<ToastAlert>(extraBufferCapacity = 16)
    val toastEvents: SharedFlow<ToastAlert> = _toastEvents.asSharedFlow()

    // Computed performance
    val performanceMetrics: StateFlow<PerformanceMetrics> = combine(
        journalTrades,
        riskEur,
        capitalEur
    ) { trades, risk, capital ->
        val closed = trades.size
        var wins = 0
        var losses = 0
        var grossWinR = 0.0
        var grossLossR = 0.0
        var totalR = 0.0

        val runningPoints = mutableListOf(capital)
        var runningBal = capital

        // Process trades from oldest to newest for equity curve
        trades.reversed().forEach { t ->
            totalR += t.rMultiple
            if (t.rMultiple > 0) {
                wins++
                grossWinR += t.rMultiple
            } else if (t.rMultiple < 0) {
                losses++
                grossLossR += kotlin.math.abs(t.rMultiple)
            }
            runningBal += t.rMultiple * risk
            runningPoints.add(runningBal)
        }

        val winRate = if (closed > 0) (wins * 100) / closed else null
        val pf = if (grossLossR > 0.0) grossWinR / grossLossR else if (grossWinR > 0.0) 99.99 else null
        val pnl = totalR * risk
        val balance = capital + pnl

        PerformanceMetrics(
            totalTrades = closed,
            wins = wins,
            losses = losses,
            winRatePct = winRate,
            totalR = totalR,
            profitFactor = pf,
            pnlEur = pnl,
            balanceEur = balance,
            equityPoints = runningPoints
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), PerformanceMetrics())

    init {
        loadCalendar()

        viewModelScope.launch {
            tradingEngine.alerts.collect { alert ->
                when (alert) {
                    is EngineAlert.NewSignal -> {
                        triggerHaptic()
                        _toastEvents.tryEmit(
                            ToastAlert(
                                symbol = alert.signal.symbol,
                                title = "${alert.signal.symbol} ${alert.signal.direction} ACTIF",
                                message = "${alert.signal.setupIctLabel()} • R:R ${alert.signal.rr}:1"
                            )
                        )
                    }
                    is EngineAlert.ExitHit -> {
                        triggerHaptic()
                        val isWin = alert.isTp
                        val rStr = alert.rMultiple?.let { if (it >= 0) "+${String.format("%.2f", it)}R" else "${String.format("%.2f", it)}R" } ?: ""
                        _toastEvents.tryEmit(
                            ToastAlert(
                                symbol = alert.signal.symbol,
                                title = if (isWin) "${alert.signal.symbol} 🎯 TP TOUCHÉ" else "${alert.signal.symbol} 🛑 SL TOUCHÉ",
                                message = if (isWin) "Gain $rStr atteint" else "Perte $rStr",
                                isWin = isWin
                            )
                        )
                    }
                }
            }
        }
    }

    private fun triggerHaptic() {
        if (!_vibrationEnabled.value) return
        try {
            val ctx = getApplication<Application>()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = ctx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vm?.defaultVibrator?.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = ctx.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                @Suppress("DEPRECATION")
                v?.vibrate(120)
            }
        } catch (e: Exception) {
            // Haptics optional
        }
    }

    fun loadCalendar(forceRefresh: Boolean = false) {
        viewModelScope.launch {
            _isCalendarLoading.value = true
            val events = calendarRepo.getCalendarEvents(forceRefresh)
            _calendarEvents.value = events
            _isCalendarLoading.value = false
        }
    }

    fun setScannerFilter(filter: ScannerFilter) {
        _scannerFilter.value = filter
    }

    fun setCalendarPeriod(period: CalendarPeriod) {
        _calendarPeriod.value = period
    }

    fun setCalendarImpact(impact: CalendarImpactFilter) {
        _calendarImpact.value = impact
    }

    fun selectAsset(symbol: String) {
        _selectedAssetSymbol.value = symbol
    }

    fun clearSelectedAsset() {
        _selectedAssetSymbol.value = null
    }

    fun resetAsset(symbol: String) {
        tradingEngine.resetAsset(symbol)
    }

    fun simulateSignal() {
        tradingEngine.triggerSimulatedSignal()
    }

    fun setRiskEur(amount: Double) {
        tradingEngine.setRiskEur(amount)
    }

    fun setCapitalEur(amount: Double) {
        tradingEngine.setCapitalEur(amount)
    }

    fun toggleAudio() {
        _audioEnabled.value = !_audioEnabled.value
    }

    fun toggleVibration() {
        _vibrationEnabled.value = !_vibrationEnabled.value
    }

    fun setServerUrl(url: String) {
        tradingEngine.setServerUrl(url)
    }

    fun connectServer() {
        tradingEngine.connectWebSocket()
    }

    fun disconnectServer() {
        tradingEngine.disconnectWebSocket()
    }
}

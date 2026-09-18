package com.example.ictradar

import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Radar
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.model.TradingAsset
import com.example.ictradar.ui.MainViewModel
import com.example.ictradar.ui.components.KillzonesHeader
import com.example.ictradar.ui.screens.CalendarScreen
import com.example.ictradar.ui.screens.ChartDetailSheet
import com.example.ictradar.ui.screens.JournalScreen
import com.example.ictradar.ui.screens.ScannerScreen
import com.example.ictradar.ui.screens.SettingsScreen
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.BgBody
import com.example.ictradar.ui.theme.BgElevated
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.ICTRadarTheme
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain

enum class MainNavTab(val title: String, val icon: ImageVector) {
    SCANNER("Scanner", Icons.Default.Radar),
    JOURNAL("Journal", Icons.Default.MenuBook),
    CALENDAR("Calendrier", Icons.Default.CalendarMonth),
    SETTINGS("Réglages", Icons.Default.Settings)
}

class MainActivity : ComponentActivity() {

    private val viewModel: MainViewModel by viewModels()
    private var toneGenerator: ToneGenerator? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        try {
            toneGenerator = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 80)
        } catch (e: Exception) {
            // Optional audio
        }

        setContent {
            ICTRadarTheme {
                MainContent(
                    viewModel = viewModel,
                    onPlaySound = { isWin ->
                        if (viewModel.audioEnabled.value) {
                            try {
                                if (isWin == true) {
                                    toneGenerator?.startTone(ToneGenerator.TONE_PROP_PROMPT, 200)
                                } else if (isWin == false) {
                                    toneGenerator?.startTone(ToneGenerator.TONE_PROP_NACK, 250)
                                } else {
                                    toneGenerator?.startTone(ToneGenerator.TONE_PROP_BEEP, 150)
                                }
                            } catch (e: Exception) {
                                // Ignore sound error
                            }
                        }
                    }
                )
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        toneGenerator?.release()
    }
}

@Composable
fun MainContent(
    viewModel: MainViewModel,
    onPlaySound: (Boolean?) -> Unit
) {
    val signals by viewModel.signals.collectAsState()
    val journalTrades by viewModel.journalTrades.collectAsState()
    val killzones by viewModel.killzones.collectAsState()
    val totalAlerts by viewModel.totalAlerts.collectAsState()
    val tpCount by viewModel.tpCount.collectAsState()
    val slCount by viewModel.slCount.collectAsState()
    val riskEur by viewModel.riskEur.collectAsState()
    val capitalEur by viewModel.capitalEur.collectAsState()
    val performanceMetrics by viewModel.performanceMetrics.collectAsState()
    val calendarEvents by viewModel.calendarEvents.collectAsState()
    val isCalendarLoading by viewModel.isCalendarLoading.collectAsState()
    val scannerFilter by viewModel.scannerFilter.collectAsState()
    val calendarPeriod by viewModel.calendarPeriod.collectAsState()
    val calendarImpact by viewModel.calendarImpact.collectAsState()
    val selectedAssetSymbol by viewModel.selectedAssetSymbol.collectAsState()
    val audioEnabled by viewModel.audioEnabled.collectAsState()
    val vibrationEnabled by viewModel.vibrationEnabled.collectAsState()
    val isServerConnected by viewModel.isServerConnected.collectAsState()
    val serverUrl by viewModel.serverUrl.collectAsState()

    val snackbarHostState = remember { SnackbarHostState() }
    var currentTab by remember { mutableStateOf(MainNavTab.SCANNER) }

    // Listen for toast/audio events
    LaunchedEffect(Unit) {
        viewModel.toastEvents.collect { alert ->
            onPlaySound(alert.isWin)
            snackbarHostState.showSnackbar(
                message = "${alert.title} — ${alert.message}"
            )
        }
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = BgBody,
        snackbarHost = { SnackbarHost(snackbarHostState) },
        bottomBar = {
            NavigationBar(
                containerColor = BgElevated,
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderColor)
            ) {
                MainNavTab.values().forEach { tab ->
                    val isSelected = currentTab == tab
                    NavigationBarItem(
                        selected = isSelected,
                        onClick = { currentTab = tab },
                        icon = {
                            Icon(
                                imageVector = tab.icon,
                                contentDescription = tab.title,
                                modifier = Modifier.size(22.dp)
                            )
                        },
                        label = {
                            Text(
                                text = tab.title,
                                fontSize = 11.sp,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                            )
                        },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = AccentBlue,
                            selectedTextColor = AccentBlue,
                            unselectedIconColor = TextFaint,
                            unselectedTextColor = TextFaint,
                            indicatorColor = AccentBlue.copy(alpha = 0.16f)
                        ),
                        modifier = Modifier.testTag("nav_tab_${tab.name.lowercase()}")
                    )
                }
            }
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .windowInsetsPadding(WindowInsets.statusBars)
        ) {
            // Killzones Institutional Header (Always accessible)
            KillzonesHeader(
                killzones = killzones,
                audioEnabled = audioEnabled,
                onToggleAudio = { viewModel.toggleAudio() },
                onSimulate = { viewModel.simulateSignal() }
            )

            // Screen switcher
            Box(modifier = Modifier.weight(1f)) {
                when (currentTab) {
                    MainNavTab.SCANNER -> {
                        ScannerScreen(
                            signals = signals,
                            totalAlerts = totalAlerts,
                            tpCount = tpCount,
                            slCount = slCount,
                            riskEur = riskEur,
                            activeFilter = scannerFilter,
                            onSelectFilter = { viewModel.setScannerFilter(it) },
                            onResetAsset = { viewModel.resetAsset(it) },
                            onOpenChart = { viewModel.selectAsset(it) }
                        )
                    }
                    MainNavTab.JOURNAL -> {
                        JournalScreen(
                            trades = journalTrades,
                            metrics = performanceMetrics,
                            riskEur = riskEur,
                            capitalEur = capitalEur,
                            onRiskChange = { viewModel.setRiskEur(it) },
                            onCapitalChange = { viewModel.setCapitalEur(it) }
                        )
                    }
                    MainNavTab.CALENDAR -> {
                        CalendarScreen(
                            events = calendarEvents,
                            isLoading = isCalendarLoading,
                            period = calendarPeriod,
                            impact = calendarImpact,
                            onSelectPeriod = { viewModel.setCalendarPeriod(it) },
                            onSelectImpact = { viewModel.setCalendarImpact(it) },
                            onRefresh = { viewModel.loadCalendar(forceRefresh = true) }
                        )
                    }
                    MainNavTab.SETTINGS -> {
                        SettingsScreen(
                            serverUrl = serverUrl,
                            isServerConnected = isServerConnected,
                            audioEnabled = audioEnabled,
                            vibrationEnabled = vibrationEnabled,
                            onServerUrlChange = { viewModel.setServerUrl(it) },
                            onConnectServer = { viewModel.connectServer() },
                            onDisconnectServer = { viewModel.disconnectServer() },
                            onToggleAudio = { viewModel.toggleAudio() },
                            onToggleVibration = { viewModel.toggleVibration() },
                            onSimulateSignal = { viewModel.simulateSignal() }
                        )
                    }
                }
            }
        }
    }

    // Chart detail bottom sheet if asset selected
    if (selectedAssetSymbol != null) {
        val asset = TradingAsset.ALL_ASSETS.find { it.symbol == selectedAssetSymbol }
        val signal = signals[selectedAssetSymbol]
        if (asset != null && signal != null) {
            ChartDetailSheet(
                asset = asset,
                signal = signal,
                riskEur = riskEur,
                onReset = { viewModel.resetAsset(asset.symbol) },
                onDismiss = { viewModel.clearSelectedAsset() }
            )
        }
    }
}

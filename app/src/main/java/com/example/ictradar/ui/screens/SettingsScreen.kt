package com.example.ictradar.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Sensors
import androidx.compose.material.icons.filled.Vibration
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.BgBody
import com.example.ictradar.ui.theme.BgCard
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.BorderSoft
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted

@Composable
fun SettingsScreen(
    serverUrl: String,
    isServerConnected: Boolean,
    audioEnabled: Boolean,
    vibrationEnabled: Boolean,
    onServerUrlChange: (String) -> Unit,
    onConnectServer: () -> Unit,
    onDisconnectServer: () -> Unit,
    onToggleAudio: () -> Unit,
    onToggleVibration: () -> Unit,
    onSimulateSignal: () -> Unit,
    modifier: Modifier = Modifier
) {
    var urlInput by remember(serverUrl) { mutableStateOf(serverUrl) }

    LazyColumn(
        modifier = modifier
            .fillMaxSize()
            .background(BgBody)
            .padding(horizontal = 14.dp),
        contentPadding = PaddingValues(top = 14.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Section: Server Connection
        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Cloud,
                            contentDescription = null,
                            tint = AccentBlue,
                            modifier = Modifier.size(18.dp)
                        )
                        Text(
                            text = "SERVEUR WEBHOOK / WEBSOCKET",
                            color = TextMain,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    // Connection status pill
                    val statusText = if (isServerConnected) "CONNECTÉ" else "AUTONOME"
                    val statusColor = if (isServerConnected) AccentGreen else AccentBlue
                    Box(
                        modifier = Modifier
                            .clip(RoundedCornerShape(6.dp))
                            .background(statusColor.copy(alpha = 0.16f))
                            .padding(horizontal = 7.dp, vertical = 3.dp)
                    ) {
                        Text(
                            text = statusText,
                            color = statusColor,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.ExtraBold,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }

                Text(
                    text = "Tu peux connecter le terminal à ton serveur FastAPI (server.py) hébergé sur Render/VPS, ou laisser le scanner interne fonctionner en mode autonome.",
                    color = TextMuted,
                    fontSize = 11.5.sp
                )

                OutlinedTextField(
                    value = urlInput,
                    onValueChange = {
                        urlInput = it
                        onServerUrlChange(it)
                    },
                    label = { Text("URL WebSocket (ex: ws://votre-serveur/ws)", fontSize = 11.sp) },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = AccentBlue,
                        unfocusedBorderColor = BorderSoft,
                        focusedTextColor = TextMain,
                        unfocusedTextColor = TextMain,
                        focusedContainerColor = BgInset,
                        unfocusedContainerColor = BgInset
                    ),
                    singleLine = true,
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("server_url_input")
                )

                Button(
                    onClick = {
                        if (isServerConnected) onDisconnectServer() else onConnectServer()
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isServerConnected) AccentRed.copy(alpha = 0.2f) else AccentBlue,
                        contentColor = if (isServerConnected) AccentRed else TextMain
                    ),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(if (isServerConnected) "Déconnecter du serveur" else "Connecter au serveur live")
                }
            }
        }

        // Section: Alert Preferences
        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                Text(
                    text = "PRÉFÉRENCES DE NOTIFICATION",
                    color = TextMuted,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.6.sp
                )

                // Audio toggle
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.VolumeUp,
                            contentDescription = null,
                            tint = if (audioEnabled) AccentGreen else TextFaint,
                            modifier = Modifier.size(20.dp)
                        )
                        Column {
                            Text("Alertes Sonores", color = TextMain, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                            Text("Bips d'entrée BUY / SELL et sorties TP/SL", color = TextMuted, fontSize = 10.5.sp)
                        }
                    }

                    Switch(
                        checked = audioEnabled,
                        onCheckedChange = { onToggleAudio() },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = TextMain,
                            checkedTrackColor = AccentBlue,
                            uncheckedThumbColor = TextFaint,
                            uncheckedTrackColor = BgInset
                        )
                    )
                }

                // Vibration toggle
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Vibration,
                            contentDescription = null,
                            tint = if (vibrationEnabled) AccentGreen else TextFaint,
                            modifier = Modifier.size(20.dp)
                        )
                        Column {
                            Text("Retours Haptiques", color = TextMain, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                            Text("Vibration lors de la réception d'un signal", color = TextMuted, fontSize = 10.5.sp)
                        }
                    }

                    Switch(
                        checked = vibrationEnabled,
                        onCheckedChange = { onToggleVibration() },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = TextMain,
                            checkedTrackColor = AccentBlue,
                            uncheckedThumbColor = TextFaint,
                            uncheckedTrackColor = BgInset
                        )
                    )
                }
            }
        }

        // Section: Diagnostics & Signal Simulator
        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Bolt,
                        contentDescription = null,
                        tint = AccentBlue,
                        modifier = Modifier.size(18.dp)
                    )
                    Text(
                        text = "TEST DU CYCLE COMPLET ICT",
                        color = TextMain,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Text(
                    text = "Génère un signal institutionnel instantané (Turtle Soup SSL/BSL ou Retest FVG) avec calcul de progression et clôture TP/SL automatique pour vérifier le journal et la courbe d'équité.",
                    color = TextMuted,
                    fontSize = 11.5.sp
                )

                Button(
                    onClick = onSimulateSignal,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AccentGreen.copy(alpha = 0.2f),
                        contentColor = AccentGreen
                    ),
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("⚡ Déclencher un signal test complet")
                }
            }
        }

        // Section: Pine Script Webhook Guide
        item {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(BgCard)
                    .border(1.dp, BorderColor, RoundedCornerShape(12.dp))
                    .padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = "FORMAT DU PAYLOAD WEBHOOK (PINE SCRIPT)",
                    color = TextMuted,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 0.6.sp
                )

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(BgInset)
                        .border(1.dp, BorderSoft, RoundedCornerShape(8.dp))
                        .padding(10.dp)
                ) {
                    Text(
                        text = "{\n" +
                                "  \"symbol\": \"GOLD\",\n" +
                                "  \"status\": \"SSL SWEEP\",\n" +
                                "  \"direction\": \"BUY\",\n" +
                                "  \"quality\": \"A+\",\n" +
                                "  \"rr\": \"2.0\",\n" +
                                "  \"entry_price\": 2580.0,\n" +
                                "  \"sl_price\": 2570.0,\n" +
                                "  \"tp_price\": 2600.0,\n" +
                                "  \"current_price\": 2580.0\n" +
                                "}",
                        color = TextFaint,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }
    }
}

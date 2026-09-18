package com.example.ictradar.ui.components

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.VolumeMute
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ictradar.data.repository.KillzoneStatus
import com.example.ictradar.ui.theme.AccentBlue
import com.example.ictradar.ui.theme.AccentGreen
import com.example.ictradar.ui.theme.AccentGreenSoft
import com.example.ictradar.ui.theme.AccentRed
import com.example.ictradar.ui.theme.AccentRedSoft
import com.example.ictradar.ui.theme.BgCard
import com.example.ictradar.ui.theme.BgElevated
import com.example.ictradar.ui.theme.BgInset
import com.example.ictradar.ui.theme.BorderColor
import com.example.ictradar.ui.theme.TextFaint
import com.example.ictradar.ui.theme.TextMain
import com.example.ictradar.ui.theme.TextMuted

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun KillzonesHeader(
    killzones: KillzoneStatus,
    audioEnabled: Boolean,
    onToggleAudio: () -> Unit,
    onSimulate: () -> Unit,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.25f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulseScale"
    )

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(BgElevated)
            .border(1.dp, BorderColor)
            .padding(14.dp)
    ) {
        // Top row: Brand + Action buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Logo badge
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .clip(RoundedCornerShape(9.dp))
                        .background(
                            Brush.linearGradient(
                                listOf(AccentBlue, AccentGreen)
                            )
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "ICT",
                        color = Color(0xFF04070D),
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 14.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Column {
                    Text(
                        text = "ICT Radar Pro",
                        color = TextMain,
                        fontWeight = FontWeight.ExtraBold,
                        fontSize = 16.sp,
                        letterSpacing = (-0.3).sp
                    )
                    Text(
                        text = "TERMINAL INSTITUTIONNEL",
                        color = TextMuted,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.8.sp
                    )
                }
            }

            // Quick Actions
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Simulation signal button
                Button(
                    onClick = onSimulate,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = AccentBlue.copy(alpha = 0.18f),
                        contentColor = AccentBlue
                    ),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 10.dp, vertical = 6.dp),
                    modifier = Modifier
                        .height(34.dp)
                        .testTag("simulate_signal_btn")
                ) {
                    Icon(
                        imageVector = Icons.Default.Bolt,
                        contentDescription = "Simulate Signal",
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "Simuler",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                // Audio toggle button
                IconButton(
                    onClick = onToggleAudio,
                    modifier = Modifier
                        .size(34.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(BgInset)
                        .border(1.dp, BorderColor, RoundedCornerShape(8.dp))
                        .testTag("audio_toggle_btn")
                ) {
                    Icon(
                        imageVector = if (audioEnabled) Icons.Default.VolumeUp else Icons.Default.VolumeMute,
                        contentDescription = "Audio toggle",
                        tint = if (audioEnabled) AccentGreen else TextFaint,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // System pill & Killzones row
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            // Live Status Pill
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .clip(RoundedCornerShape(16.dp))
                    .background(BgInset)
                    .border(1.dp, BorderColor, RoundedCornerShape(16.dp))
                    .padding(horizontal = 10.dp, vertical = 5.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .scale(pulseScale)
                        .clip(CircleShape)
                        .background(AccentGreen)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "LIVE",
                    color = AccentGreen,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = killzones.utcTime,
                    color = TextMuted,
                    fontSize = 10.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            // London Killzone
            KillzoneBadge(
                label = "🇬🇧 LONDRES",
                isActive = killzones.isLondonActive
            )

            // NY AM Killzone
            KillzoneBadge(
                label = "🇺🇸 NY AM",
                isActive = killzones.isNyAmActive
            )
        }
    }
}

@Composable
private fun KillzoneBadge(
    label: String,
    isActive: Boolean
) {
    val bg = if (isActive) AccentGreenSoft else BgInset
    val border = if (isActive) AccentGreen.copy(alpha = 0.5f) else BorderColor
    val textColor = if (isActive) AccentGreen else TextFaint

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .background(bg)
            .border(1.dp, border, RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 5.dp)
    ) {
        Text(
            text = label,
            color = if (isActive) TextMain else TextFaint,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = if (isActive) "ACTIVE" else "FERMÉE",
            color = textColor,
            fontSize = 9.sp,
            fontWeight = FontWeight.ExtraBold,
            fontFamily = FontFamily.Monospace
        )
    }
}

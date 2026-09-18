package com.example.ictradar.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = AccentBlue,
    onPrimary = TextMain,
    primaryContainer = AccentBlueSoft,
    onPrimaryContainer = AccentBlue,
    secondary = AccentGreen,
    onSecondary = BgBody,
    secondaryContainer = AccentGreenSoft,
    onSecondaryContainer = AccentGreen,
    error = AccentRed,
    errorContainer = AccentRedSoft,
    onError = TextMain,
    background = BgBody,
    onBackground = TextMain,
    surface = BgElevated,
    onSurface = TextMain,
    surfaceVariant = BgCard,
    onSurfaceVariant = TextMuted,
    outline = BorderColor,
    outlineVariant = BorderSoft
)

@Composable
fun ICTRadarTheme(
    darkTheme: Boolean = true,
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}

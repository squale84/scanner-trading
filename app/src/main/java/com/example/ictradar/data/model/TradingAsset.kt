package com.example.ictradar.data.model

enum class AssetCategory {
    TRAD,
    CRYPTO
}

data class TradingAsset(
    val symbol: String,
    val name: String,
    val category: AssetCategory,
    val tvSymbol: String,
    val initialPrice: Double,
    val decimals: Int = 2
) {
    companion object {
        val ALL_ASSETS = listOf(
            // TradFi
            TradingAsset("GOLD", "XAU/USD • OR COMPTANT", AssetCategory.TRAD, "OANDA:XAUUSD", 2580.50, 2),
            TradingAsset("US100", "NASDAQ 100 INDEX", AssetCategory.TRAD, "OANDA:NAS100USD", 19840.0, 2),
            TradingAsset("SPX500", "S&P 500 INDEX", AssetCategory.TRAD, "OANDA:SPX500USD", 5620.0, 2),
            TradingAsset("GER40", "DAX 40 INDEX", AssetCategory.TRAD, "CAPITALCOM:DE40", 18650.0, 1),
            TradingAsset("FR40", "CAC 40 INDEX", AssetCategory.TRAD, "OANDA:FR40EUR", 7510.0, 1),
            TradingAsset("USOIL", "CRUDE OIL (WTI)", AssetCategory.TRAD, "TVC:USOIL", 71.40, 2),
            TradingAsset("NATGAS", "GAZ NATUREL", AssetCategory.TRAD, "CAPITALCOM:NATURALGAS", 2.38, 3),
            TradingAsset("EURUSD", "EURO / US DOLLAR", AssetCategory.TRAD, "FX:EURUSD", 1.0850, 5),
            TradingAsset("USDJPY", "US DOLLAR / YEN JAPONAIS", AssetCategory.TRAD, "FX:USDJPY", 143.20, 3),

            // Crypto
            TradingAsset("BTCUSD", "BITCOIN / USD", AssetCategory.CRYPTO, "BINANCE:BTCUSDT", 63800.0, 2),
            TradingAsset("ETHUSD", "ETHEREUM / USD", AssetCategory.CRYPTO, "BINANCE:ETHUSDT", 2560.0, 2),
            TradingAsset("SOLUSD", "SOLANA / USD", AssetCategory.CRYPTO, "BINANCE:SOLUSDT", 148.50, 2),
            TradingAsset("ADAUSDT", "CARDANO / USDT", AssetCategory.CRYPTO, "BINANCE:ADAUSDT", 0.3540, 4),
            TradingAsset("DOGEUSDT", "DOGECOIN / USDT", AssetCategory.CRYPTO, "BINANCE:DOGEUSDT", 0.1060, 4)
        )
    }
}

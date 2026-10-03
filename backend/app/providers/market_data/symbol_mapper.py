from typing import Tuple, Dict

# Standard Yahoo Finance index ticker mappings for Indian markets
INDEX_CANONICAL_TO_PROVIDER: Dict[str, str] = {
    "NIFTY 50": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY": "^NSEI",
    "^NSEI": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTY BANK": "^NSEBANK",
    "^NSEBANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "BSE SENSEX": "^BSESN",
    "^BSESN": "^BSESN",
    "INDIA VIX": "^INDIAVIX",
    "INDIAVIX": "^INDIAVIX",
    "^INDIAVIX": "^INDIAVIX",
}

INDEX_PROVIDER_TO_CANONICAL: Dict[str, Tuple[str, str]] = {
    "^NSEI": ("NIFTY 50", "NSE"),
    "^NSEBANK": ("BANKNIFTY", "NSE"),
    "^BSESN": ("SENSEX", "BSE"),
    "^INDIAVIX": ("INDIA VIX", "NSE"),
}


class IndianSymbolMapper:
    """Centralized symbol mapping system for Indian equities and indices."""

    @staticmethod
    def to_provider_symbol(symbol: str, exchange: str = "NSE") -> str:
        """
        Convert canonical application symbol to Yahoo Finance / provider symbol.
        Does NOT blindly append .NS if an exchange suffix or index prefix already exists.
        """
        clean = (symbol or "").strip()
        upper = clean.upper()

        if upper in INDEX_CANONICAL_TO_PROVIDER:
            return INDEX_CANONICAL_TO_PROVIDER[upper]

        # Already has Yahoo Finance Indian suffix or symbol indicator
        if upper.endswith(".NS") or upper.endswith(".BO") or upper.startswith("^"):
            return upper

        ex_upper = (exchange or "NSE").strip().upper()
        if ex_upper == "BSE":
            return f"{upper}.BO"
        return f"{upper}.NS"

    @staticmethod
    def to_canonical_symbol(provider_symbol: str) -> Tuple[str, str]:
        """
        Convert external provider symbol to canonical application (symbol, exchange).
        Example:
            'RELIANCE.NS' -> ('RELIANCE', 'NSE')
            'TCS.BO'      -> ('TCS', 'BSE')
            '^NSEI'       -> ('NIFTY 50', 'NSE')
        """
        clean = (provider_symbol or "").strip()
        upper = clean.upper()

        if upper in INDEX_PROVIDER_TO_CANONICAL:
            return INDEX_PROVIDER_TO_CANONICAL[upper]

        if upper.endswith(".NS"):
            return upper[:-3], "NSE"
        elif upper.endswith(".BO"):
            return upper[:-3], "BSE"
        elif upper.startswith("^"):
            return upper, "INDEX"

        return upper, "NSE"

# app/core/fx.py
#
# Fetches live exchange rates from the Frankfurter API (free, no API key needed).
# Used when an expense is entered in a currency different from the group's base currency.

import httpx
from fastapi import HTTPException


async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    Returns the exchange rate from from_currency to to_currency.
    If both are the same, returns 1.0 immediately (no network call).

    Raises HTTP 503 if Frankfurter is unreachable.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return 1.0

    url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return float(data["rates"][to_currency])
    except Exception:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Could not fetch exchange rate from {from_currency} to {to_currency}. "
                "The Frankfurter API may be temporarily unavailable. Try again shortly."
            ),
        )

import requests
from datetime import timedelta
from django.utils import timezone
from .models import RateCache

class RateService:
    API_URL = "https://api.frankfurter.app/latest?from=USD"
    CURRENCIES = ["NGN", "GHS", "KES", "ZAR", "USD"]

    @classmethod
    def fetch_rates_from_api(cls):
        """Fetch from public API and build full rate matrix"""
        try:
            resp = requests.get(cls.API_URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            usd_rates = data["rates"]

            # Build full matrix (NGN→GHS, GHS→NGN, etc.)
            matrix = {}
            for from_curr in cls.CURRENCIES:
                matrix[from_curr] = {}
                for to_curr in cls.CURRENCIES:
                    if from_curr == to_curr:
                        matrix[from_curr][to_curr] = 1.0
                        continue
                    if from_curr == "USD":
                        rate = usd_rates.get(to_curr, 1.0)
                    elif to_curr == "USD":
                        rate = 1.0 / usd_rates.get(from_curr, 1.0)
                    else:
                        # cross-rate via USD
                        rate = usd_rates.get(to_curr, 1.0) / usd_rates.get(from_curr, 1.0)
                    matrix[from_curr][to_curr] = round(float(rate), 6)

            cache_data = {
                **matrix,
                "fetched_at": timezone.now().isoformat(),
                "stale": False
            }

            RateCache.objects.create(
                base_currency="USD",
                rates=cache_data,
                fetched_at=timezone.now(),
                stale=False
            )
            return cache_data
        except Exception as e:
            print(f"❌ Rate API failed: {e}")
            return None

    @classmethod
    def get_cached_rates(cls):
        """Always read from DB. Refresh only if >30 min old (never on every request)"""
        latest = RateCache.objects.last()
        if not latest:
            return cls.fetch_rates_from_api()

        if timezone.now() - latest.fetched_at > timedelta(minutes=30):
            new_rates = cls.fetch_rates_from_api()
            if new_rates:
                return new_rates
            # API down → mark as stale
            latest.stale = True
            latest.save(update_fields=["stale"])
            return {**latest.rates, "stale": True}

        return {**latest.rates, "stale": latest.stale}

    @classmethod
    def convert_price(cls, price: float, from_currency: str, to_currency: str):
        """Core conversion logic used by products"""
        rates = cls.get_cached_rates()
        if from_currency not in rates or to_currency not in rates[from_currency]:
            raise ValueError(f"No rate for {from_currency} → {to_currency}")
        rate = rates[from_currency][to_currency]
        return round(price * rate, 2)
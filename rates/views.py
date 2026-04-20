from rest_framework.views import APIView
from rest_framework.response import Response
from .services import RateService

class RateView(APIView):
    def get(self, request):
        rates = RateService.get_cached_rates()
        return Response({
            "error": False,
            "rates": rates,
            "fetched_at": rates.get("fetched_at"),
            "stale": rates.get("stale", False)
        })

from time import monotonic
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        start = monotonic()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            duration_ms = int((monotonic() - start) * 1000)
            return Response(
                {
                    "status": "ok",
                    "db": "ok",
                    "db_name": connection.settings_dict.get("NAME"),
                    "duration_ms": duration_ms,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            duration_ms = int((monotonic() - start) * 1000)
            return Response(
                {
                    "status": "error",
                    "db": "unavailable",
                    "error": str(exc),
                    "duration_ms": duration_ms,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

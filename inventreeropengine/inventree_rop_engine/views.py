"""
Simple test views for ROP plugin to verify routing works.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TestView(APIView):
    """Simple test endpoint to verify plugin routing works."""

    def get(self, request):
        """Return a simple test response."""
        return Response({
            'status': 'ok',
            'message': 'ROP Engine plugin is working',
            'plugin': 'inventree-rop-engine',
            'version': '0.1.0'
        }, status=status.HTTP_200_OK)

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SimilarityAnalysisViewSet

router = DefaultRouter()
router.register("similarities", SimilarityAnalysisViewSet, basename="similarity")

urlpatterns = [
    path("", include(router.urls)),
]
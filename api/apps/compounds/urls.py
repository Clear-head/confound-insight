from rest_framework.routers import DefaultRouter

from .views import CompoundViewSet

router = DefaultRouter()
router.register('compounds', CompoundViewSet, basename='compounds')
urlpatterns = router.urls
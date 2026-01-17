from rest_framework.routers import DefaultRouter

from apps.products.views import ProductViewSet, ProductIngredientViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='products')
router.register('ingredients', ProductIngredientViewSet, basename='ingredients')
urlpatterns = router.urls
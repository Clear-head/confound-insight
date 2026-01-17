from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Prefetch

from .models import Product, ProductIngredient
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    ProductIngredientSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    """
    의약품 제품 ViewSet

    list: 제품 목록 조회 (검색/필터링 지원)
    retrieve: 제품 상세 조회 (성분 포함)
    create: 제품 생성
    update: 제품 전체 수정
    partial_update: 제품 부분 수정
    destroy: 제품 삭제
    """

    queryset = Product.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product_name', 'permit_number', 'manufacturer']
    ordering_fields = ['created_at', 'updated_at', 'product_name']
    ordering = ['-created_at']

    def get_queryset(self):
        """
            쿼리셋  필터링
        """
        queryset = super().get_queryset()

        if self.action == 'list':
            queryset = queryset.annotate(
                ingredient_count=Count('ingredients', filter=Q(ingredients__is_main_active=True))
            )

        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'ingredients',
                    queryset=ProductIngredient.objects.select_related('compound')
                )
            )

        # 쿼리 파라미터 필터링
        is_combination = self.request.query_params.get('is_combination')

        if is_combination is not None:
            is_combination_bool = is_combination.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_combination=is_combination_bool)

        manufacturer = self.request.query_params.get('manufacturer')

        if manufacturer:
            queryset = queryset.filter(manufacturer__icontains=manufacturer)

        return queryset

    def get_serializer_class(self):
        """
        액션별 Serializer 선택
        """
        if self.action == 'list':
            return ProductListSerializer

        elif self.action == 'create':
            return ProductCreateSerializer

        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer

        return ProductDetailSerializer

    @action(detail=True, methods=['get'])
    def ingredients(self, request, pk=None):
        """
        제품의 성분 목록 조회

        GET /api/products/{id}/ingredients/

        Query Parameters:
        - is_main_active: true/false (주성분만 필터링)
        - normalization_status: PENDING/SUCCESS/FAILED/MANUAL
        """
        product = self.get_object()
        ingredients = product.ingredients.select_related('compound')

        # 필터링
        is_main_active = request.query_params.get('is_main_active')

        if is_main_active is not None:
            is_main_active_bool = is_main_active.lower() in ['true', '1', 'yes']
            ingredients = ingredients.filter(is_main_active=is_main_active_bool)

        normalization_status = request.query_params.get('normalization_status')

        if normalization_status:
            ingredients = ingredients.filter(
                normalization_status=normalization_status.upper()
            )

        serializer = ProductIngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        제품 통계 정보

        GET /api/products/statistics/
        """
        total_count = Product.objects.count()
        combination_count = Product.objects.filter(is_combination=True).count()
        single_count = total_count - combination_count

        # 제조사별 제품 수 Top 10
        top_manufacturers = (
            Product.objects
            .values('manufacturer')
            .annotate(product_count=Count('id'))
            .order_by('-product_count')[:10]
        )

        return Response({
            'total_products': total_count,
            'combination_products': combination_count,
            'single_products': single_count,
            'top_manufacturers': list(top_manufacturers),
        })

    def destroy(self, request, *args, **kwargs):
        """
        제품 삭제 (관련 성분 정보도 CASCADE로 함께 삭제됨)
        """
        instance = self.get_object()
        product_name = instance.product_name

        self.perform_destroy(instance)

        return Response({
            'message': f'제품 "{product_name}"이(가) 삭제되었습니다.',
        }, status=status.HTTP_204_NO_CONTENT)


class ProductIngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    제품-성분 매핑 ViewSet (읽기 전용)

    list: 모든 제품-성분 매핑 조회
    retrieve: 특정 매핑 상세 조회
    """

    queryset = ProductIngredient.objects.select_related('product', 'compound')
    serializer_class = ProductIngredientSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['raw_ingredient_name', 'product__product_name']
    ordering_fields = ['created_at', 'normalization_status']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        쿼리 파라미터 필터링
        """
        queryset = super().get_queryset()

        # 정규화 상태
        normalization_status = self.request.query_params.get('normalization_status')
        if normalization_status:
            queryset = queryset.filter(
                normalization_status=normalization_status.upper()
            )

        # 주성분 여부
        is_main_active = self.request.query_params.get('is_main_active')
        if is_main_active is not None:
            is_main_active_bool = is_main_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_main_active=is_main_active_bool)

        # 특정 제품의 성분만 조회
        product_id = self.request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)

        return queryset

    @action(detail=False, methods=['get'])
    def failed_normalizations(self, request):
        """
        정규화 실패한 성분 목록

        GET /api/ingredients/failed_normalizations/
        """
        failed_ingredients = (
            self.get_queryset()
            .filter(normalization_status='FAILED')
            .values('raw_ingredient_name')
            .annotate(failure_count=Count('id'))
            .order_by('-failure_count')
        )

        return Response({
            'total_failed': failed_ingredients.count(),
            'failed_ingredients': list(failed_ingredients),
        })
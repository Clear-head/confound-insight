from dataclasses import asdict

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Prefetch, Q

from .models import Product, ProductIngredient
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    ProductIngredientSerializer,
)
from .services import (
    product_service,
    product_ingredient_service,
    ProductFilterParams,
    IngredientFilterParams,
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
    search_fields = ["product_name", "permit_number", "manufacturer"]
    ordering_fields = ["created_at", "updated_at", "product_name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        쿼리셋 필터링 및 최적화
        """
        queryset = super().get_queryset()

        # 액션별 쿼리 최적화
        if self.action == "list":
            queryset = queryset.annotate(
                ingredient_count=Count(
                    "ingredients",
                    filter=Q(ingredients__is_main_active=True)
                )
            )

        elif self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "ingredients",
                    queryset=ProductIngredient.objects.select_related("compound")
                )
            )

        # 서비스 레이어를 통한 필터링
        filter_params = self._build_filter_params()
        queryset = product_service.filter_products(queryset, filter_params)

        return queryset

    def _build_filter_params(self) -> ProductFilterParams:
        """쿼리 파라미터를 ProductFilterParams로 변환"""
        params = self.request.query_params

        is_combination = params.get("is_combination")
        manufacturer = params.get("manufacturer")

        return ProductFilterParams(
            is_combination=self._parse_bool(is_combination),
            manufacturer=manufacturer,
        )

    @staticmethod
    def _parse_bool(value: str | None) -> bool | None:
        """문자열을 bool로 변환"""
        if value is None:
            return None
        return value.lower() in ["true", "1", "yes"]

    def get_serializer_class(self):
        """
        액션별 Serializer 선택
        """
        if self.action == "list":
            return ProductListSerializer

        elif self.action == "create":
            return ProductCreateSerializer

        elif self.action in ["update", "partial_update"]:
            return ProductUpdateSerializer

        return ProductDetailSerializer

    @action(detail=True, methods=["get"])
    def ingredients(self, request, pk=None):
        """
        제품의 성분 목록 조회

        GET /api/products/{id}/ingredients/

        Query Parameters:
        - is_main_active: true/false (주성분만 필터링)
        - normalization_status: PENDING/SUCCESS/FAILED/MANUAL
        """
        product = self.get_object()

        is_main_active = self._parse_bool(
            request.query_params.get("is_main_active")
        )
        normalization_status = request.query_params.get("normalization_status")

        ingredients = product_service.get_product_ingredients(
            product, is_main_active, normalization_status
        )

        serializer = ProductIngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        제품 통계 정보

        GET /api/products/statistics/
        """
        stats = product_service.get_statistics()
        return Response(asdict(stats))

    def destroy(self, request, *args, **kwargs):
        """
        제품 삭제 (관련 성분 정보도 CASCADE로 함께 삭제됨)
        """
        instance = self.get_object()
        product_name = instance.product_name

        self.perform_destroy(instance)

        return Response(
            {"message": f'제품 "{product_name}"이(가) 삭제되었습니다.'},
            status=status.HTTP_204_NO_CONTENT
        )


class ProductIngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    제품-성분 매핑 ViewSet (읽기 전용)

    list: 모든 제품-성분 매핑 조회
    retrieve: 특정 매핑 상세 조회
    """

    queryset = ProductIngredient.objects.select_related("product", "compound")
    serializer_class = ProductIngredientSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["raw_ingredient_name", "product__product_name"]
    ordering_fields = ["created_at", "normalization_status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        쿼리셋 필터링
        """
        queryset = super().get_queryset()

        # 서비스 레이어를 통한 필터링
        filter_params = self._build_filter_params()
        queryset = product_ingredient_service.filter_ingredients(
            queryset, filter_params
        )

        return queryset

    def _build_filter_params(self) -> IngredientFilterParams:
        """쿼리 파라미터를 IngredientFilterParams로 변환"""
        params = self.request.query_params

        normalization_status = params.get("normalization_status")
        is_main_active = params.get("is_main_active")
        product_id = params.get("product_id")

        return IngredientFilterParams(
            normalization_status=normalization_status,
            is_main_active=self._parse_bool(is_main_active),
            product_id=int(product_id) if product_id else None,
        )

    @staticmethod
    def _parse_bool(value: str | None) -> bool | None:
        """문자열을 bool로 변환"""
        if value is None:
            return None
        return value.lower() in ["true", "1", "yes"]

    @action(detail=False, methods=["get"])
    def failed_normalizations(self, request):
        """
        정규화 실패한 성분 목록

        GET /api/ingredients/failed_normalizations/
        """
        result = product_ingredient_service.get_failed_normalizations(
            self.get_queryset()
        )
        return Response(asdict(result))
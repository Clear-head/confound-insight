from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from django.db.models import Count, QuerySet

if TYPE_CHECKING:
    from .models import Product


@dataclass
class ProductFilterParams:
    """제품 필터링 파라미터"""
    is_combination: Optional[bool] = None
    manufacturer: Optional[str] = None


@dataclass
class IngredientFilterParams:
    """성분 필터링 파라미터"""
    normalization_status: Optional[str] = None
    is_main_active: Optional[bool] = None
    product_id: Optional[int] = None


@dataclass
class ProductStatistics:
    """제품 통계 결과"""
    total_products: int
    combination_products: int
    single_products: int
    top_manufacturers: list[dict]


@dataclass
class FailedNormalizationResult:
    """정규화 실패 결과"""
    total_failed: int
    failed_ingredients: list[dict]


class ProductService:
    """제품 비즈니스 로직 서비스"""

    def filter_products(
        self,
        queryset: QuerySet,
        params: ProductFilterParams,
    ) -> QuerySet:
        """
        제품 쿼리셋 필터링

        Args:
            queryset: 기본 쿼리셋
            params: 필터링 파라미터

        Returns:
            필터링된 쿼리셋
        """
        if params.is_combination is not None:
            queryset = queryset.filter(is_combination=params.is_combination)

        if params.manufacturer:
            queryset = queryset.filter(manufacturer__icontains=params.manufacturer)

        return queryset

    def get_statistics(self) -> ProductStatistics:
        """
        제품 전체 통계 조회

        Returns:
            통계 정보 dataclass
        """
        from .models import Product

        total_count = Product.objects.count()
        combination_count = Product.objects.filter(is_combination=True).count()

        top_manufacturers = list(
            Product.objects
            .values("manufacturer")
            .annotate(product_count=Count("id"))
            .order_by("-product_count")[:10]
        )

        return ProductStatistics(
            total_products=total_count,
            combination_products=combination_count,
            single_products=total_count - combination_count,
            top_manufacturers=top_manufacturers,
        )

    def get_product_ingredients(
        self,
        product: "Product",
        is_main_active: Optional[bool] = None,
        normalization_status: Optional[str] = None,
    ) -> QuerySet:
        """
        제품의 성분 목록 조회

        Args:
            product: 제품 객체
            is_main_active: 주성분 여부 필터
            normalization_status: 정규화 상태 필터

        Returns:
            성분 쿼리셋
        """
        ingredients = product.ingredients.select_related("compound")

        if is_main_active is not None:
            ingredients = ingredients.filter(is_main_active=is_main_active)

        if normalization_status:
            ingredients = ingredients.filter(
                normalization_status=normalization_status.upper()
            )

        return ingredients


class ProductIngredientService:
    """제품-성분 매핑 비즈니스 로직 서비스"""

    def filter_ingredients(
        self,
        queryset: QuerySet,
        params: IngredientFilterParams,
    ) -> QuerySet:
        """
        성분 쿼리셋 필터링

        Args:
            queryset: 기본 쿼리셋
            params: 필터링 파라미터

        Returns:
            필터링된 쿼리셋
        """
        if params.normalization_status:
            queryset = queryset.filter(
                normalization_status=params.normalization_status.upper()
            )

        if params.is_main_active is not None:
            queryset = queryset.filter(is_main_active=params.is_main_active)

        if params.product_id:
            queryset = queryset.filter(product_id=params.product_id)

        return queryset

    def get_failed_normalizations(
        self,
        queryset: QuerySet,
    ) -> FailedNormalizationResult:
        """
        정규화 실패한 성분 목록 조회

        Args:
            queryset: 기본 쿼리셋 (필터링된 상태 가능)

        Returns:
            실패 결과 dataclass
        """
        failed_ingredients = list(
            queryset
            .filter(normalization_status="FAILED")
            .values("raw_ingredient_name")
            .annotate(failure_count=Count("id"))
            .order_by("-failure_count")
        )

        return FailedNormalizationResult(
            total_failed=len(failed_ingredients),
            failed_ingredients=failed_ingredients,
        )


product_service = ProductService()
product_ingredient_service = ProductIngredientService()

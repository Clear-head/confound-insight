from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from django.db.models import Q, QuerySet

if TYPE_CHECKING:
    from .models import Compound
    from apps.analysis.services import SimilarCompoundResult


@dataclass
class CompoundFilterParams:
    """화합물 필터링 파라미터"""
    is_valid: Optional[bool] = None
    has_structure: Optional[bool] = None
    has_cid: Optional[bool] = None
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None


@dataclass
class CompoundStatistics:
    """화합물 통계 결과"""
    total_compounds: int
    valid_compounds: int
    invalid_compounds: int
    with_pubchem_cid: int
    with_structure_data: int
    weight_distribution: dict


@dataclass
class CompoundProductInfo:
    """화합물 포함 제품 정보"""
    id: int
    product_name: str
    permit_number: str
    manufacturer: Optional[str]
    is_main_active: bool
    content: Optional[str]
    unit: Optional[str]


class CompoundService:
    """화합물 비즈니스 로직 서비스"""

    def filter_compounds(
        self,
        queryset: QuerySet,
        params: CompoundFilterParams,
    ) -> QuerySet:
        """
        화합물 쿼리셋 필터링

        Args:
            queryset: 기본 쿼리셋
            params: 필터링 파라미터

        Returns:
            필터링된 쿼리셋
        """
        if params.is_valid is not None:
            queryset = queryset.filter(is_valid=params.is_valid)

        if params.has_structure is not None:
            if params.has_structure:
                queryset = queryset.filter(
                    smiles__isnull=False,
                    fingerprint_morgan__isnull=False
                ).exclude(smiles="")
            else:
                queryset = queryset.filter(
                    Q(smiles__isnull=True) | Q(smiles="") |
                    Q(fingerprint_morgan__isnull=True)
                )

        if params.has_cid is not None:
            if params.has_cid:
                queryset = queryset.filter(cid__isnull=False)
            else:
                queryset = queryset.filter(cid__isnull=True)

        if params.min_weight is not None:
            queryset = queryset.filter(molecular_weight__gte=params.min_weight)

        if params.max_weight is not None:
            queryset = queryset.filter(molecular_weight__lte=params.max_weight)

        return queryset

    def get_statistics(self) -> CompoundStatistics:
        """
        화합물 전체 통계 조회

        Returns:
            통계 정보 dataclass
        """
        from .models import Compound

        total_count = Compound.objects.count()
        valid_count = Compound.objects.filter(is_valid=True).count()

        with_cid_count = Compound.objects.filter(cid__isnull=False).count()
        with_structure_count = Compound.objects.filter(
            smiles__isnull=False,
            fingerprint_morgan__isnull=False
        ).exclude(smiles="").count()

        weight_distribution = {
            "under_200": Compound.objects.filter(molecular_weight__lt=200).count(),
            "200_to_500": Compound.objects.filter(
                molecular_weight__gte=200,
                molecular_weight__lt=500
            ).count(),
            "500_to_1000": Compound.objects.filter(
                molecular_weight__gte=500,
                molecular_weight__lt=1000
            ).count(),
            "over_1000": Compound.objects.filter(molecular_weight__gte=1000).count(),
            "unknown": Compound.objects.filter(molecular_weight__isnull=True).count(),
        }

        return CompoundStatistics(
            total_compounds=total_count,
            valid_compounds=valid_count,
            invalid_compounds=total_count - valid_count,
            with_pubchem_cid=with_cid_count,
            with_structure_data=with_structure_count,
            weight_distribution=weight_distribution,
        )

    def search_compounds(
        self,
        query: str,
        search_type: str = "name",
    ) -> list["Compound"]:
        """
        화합물 검색

        Args:
            query: 검색어
            search_type: 검색 타입 (name, cid, smiles)

        Returns:
            검색 결과 리스트 (Compound 객체)

        Raises:
            ValueError: 유효하지 않은 검색어 또는 타입
        """
        from .models import Compound

        query = query.strip()
        if not query:
            raise ValueError("검색어(q)를 입력해주세요.")

        search_type = search_type.lower()
        queryset = Compound.objects.all()

        if search_type == "cid":
            try:
                cid_value = int(query)
                return list(queryset.filter(cid=cid_value))
            except ValueError:
                raise ValueError("CID는 숫자여야 합니다.")

        elif search_type == "smiles":
            return list(queryset.filter(
                Q(smiles__exact=query) | Q(smiles__icontains=query)
            ))

        else:  # name (기본)
            exact_match = queryset.filter(standard_name__iexact=query)
            partial_match = queryset.filter(
                Q(standard_name__icontains=query) |
                Q(iupac_name__icontains=query)
            ).exclude(standard_name__iexact=query)

            return list(exact_match) + list(partial_match)

    def get_compound_products(
        self,
        compound: "Compound",
        is_main_active: Optional[bool] = None,
    ) -> list[CompoundProductInfo]:
        """
        화합물이 포함된 제품 목록 조회

        Args:
            compound: 화합물 객체
            is_main_active: 주성분 여부 필터 (None이면 전체)

        Returns:
            제품 정보 리스트
        """
        product_ingredients = compound.products.select_related("product")

        if is_main_active is not None:
            product_ingredients = product_ingredients.filter(
                is_main_active=is_main_active
            )

        return [
            CompoundProductInfo(
                id=pi.product.id,
                product_name=pi.product.product_name,
                permit_number=pi.product.permit_number,
                manufacturer=pi.product.manufacturer,
                is_main_active=pi.is_main_active,
                content=pi.content,
                unit=pi.unit,
            )
            for pi in product_ingredients
        ]

    def get_similar_compounds(
        self,
        compound: "Compound",
        min_score: float = 0.7,
        limit: int = 10,
    ) -> list["SimilarCompoundResult"]:
        """
        유사 화합물 목록 조회 (Tanimoto 유사도 기반)

        Args:
            compound: 대상 화합물 객체
            min_score: 최소 유사도 점수
            limit: 결과 수 제한

        Returns:
            유사 화합물 리스트
        """
        from apps.analysis.services import similarity_analysis_service

        return similarity_analysis_service.get_similar_compounds(
            compound, min_score, limit
        )


compound_service = CompoundService()
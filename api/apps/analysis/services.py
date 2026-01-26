from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from django.db.models import Avg, Count, Q, QuerySet

if TYPE_CHECKING:
    from apps.compounds.models import Compound


@dataclass
class SimilarityFilterParams:
    """유사도 분석 필터링 파라미터"""
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    fingerprint_method: Optional[str] = None
    is_current: Optional[bool] = None
    compound_id: Optional[int] = None


@dataclass
class SimilarityStatistics:
    """유사도 분석 통계"""
    total_analyses: int
    current_analyses: int
    average_score: float
    score_distribution: dict
    method_distribution: dict


@dataclass
class SimilarCompoundResult:
    """유사 화합물 결과"""
    id: int
    standard_name: str
    cid: Optional[int]
    molecular_formula: Optional[str]
    similarity_score: float
    fingerprint_method: str


class SimilarityAnalysisService:
    """유사도 분석 비즈니스 로직 서비스"""

    def filter_analyses(
        self,
        queryset: QuerySet,
        params: SimilarityFilterParams,
    ) -> QuerySet:
        """
        유사도 분석 쿼리셋 필터링

        Args:
            queryset: 기본 쿼리셋
            params: 필터링 파라미터

        Returns:
            필터링된 쿼리셋
        """
        if params.min_score is not None:
            queryset = queryset.filter(similarity_score__gte=params.min_score)

        if params.max_score is not None:
            queryset = queryset.filter(similarity_score__lte=params.max_score)

        if params.fingerprint_method:
            queryset = queryset.filter(fingerprint_method=params.fingerprint_method)

        if params.is_current is not None:
            queryset = queryset.filter(is_current=params.is_current)

        if params.compound_id is not None:
            queryset = queryset.filter(
                Q(target_compound_id=params.compound_id) |
                Q(similar_compound_id=params.compound_id)
            )

        return queryset

    def get_statistics(self) -> SimilarityStatistics:
        """
        유사도 분석 통계 조회

        Returns:
            통계 정보 dataclass
        """
        from .models import SimilarityAnalysis

        total_count = SimilarityAnalysis.objects.count()
        current_count = SimilarityAnalysis.objects.filter(is_current=True).count()

        avg_result = SimilarityAnalysis.objects.aggregate(avg=Avg("similarity_score"))
        average_score = avg_result["avg"] or 0.0

        # 유사도 점수 분포
        score_distribution = {
            "0.9_to_1.0": SimilarityAnalysis.objects.filter(
                similarity_score__gte=0.9
            ).count(),
            "0.8_to_0.9": SimilarityAnalysis.objects.filter(
                similarity_score__gte=0.8,
                similarity_score__lt=0.9
            ).count(),
            "0.7_to_0.8": SimilarityAnalysis.objects.filter(
                similarity_score__gte=0.7,
                similarity_score__lt=0.8
            ).count(),
            "below_0.7": SimilarityAnalysis.objects.filter(
                similarity_score__lt=0.7
            ).count(),
        }

        # fingerprint 방법별 분포
        method_distribution = list(
            SimilarityAnalysis.objects
            .values("fingerprint_method")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return SimilarityStatistics(
            total_analyses=total_count,
            current_analyses=current_count,
            average_score=round(average_score, 4),
            score_distribution=score_distribution,
            method_distribution=method_distribution,
        )

    def get_similar_compounds(
        self,
        compound: "Compound",
        min_score: float = 0.7,
        limit: int = 10,
    ) -> list[SimilarCompoundResult]:
        """
        특정 화합물의 유사 화합물 목록 조회

        Args:
            compound: 대상 화합물 객체
            min_score: 최소 유사도 점수
            limit: 결과 수 제한

        Returns:
            유사 화합물 리스트
        """
        from .models import SimilarityAnalysis

        similarities = SimilarityAnalysis.objects.filter(
            Q(target_compound=compound) | Q(similar_compound=compound),
            similarity_score__gte=min_score,
            is_current=True,
        ).select_related(
            "target_compound", "similar_compound"
        ).order_by("-similarity_score")[:limit]

        results = []
        for sim in similarities:
            if sim.target_compound_id == compound.id:
                other = sim.similar_compound
            else:
                other = sim.target_compound

            results.append(SimilarCompoundResult(
                id=other.id,
                standard_name=other.standard_name,
                cid=other.cid,
                molecular_formula=other.molecular_formula,
                similarity_score=sim.similarity_score,
                fingerprint_method=sim.fingerprint_method,
            ))

        return results

    def invalidate_compound_similarities(
        self,
        compound_id: int,
    ) -> int:
        """
        특정 화합물 관련 유사도 분석 무효화

        Args:
            compound_id: 화합물 ID

        Returns:
            무효화된 레코드 수
        """
        from .models import SimilarityAnalysis

        updated = SimilarityAnalysis.objects.filter(
            Q(target_compound_id=compound_id) | Q(similar_compound_id=compound_id),
            is_current=True,
        ).update(is_current=False)

        return updated


similarity_analysis_service = SimilarityAnalysisService()
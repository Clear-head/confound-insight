from dataclasses import asdict

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SimilarityAnalysis
from .serializers import (
    SimilarityAnalysisListSerializer,
    SimilarityAnalysisDetailSerializer,
    SimilarityAnalysisCreateSerializer,
)
from .services import (
    similarity_analysis_service,
    SimilarityFilterParams,
)


class SimilarityAnalysisViewSet(viewsets.ModelViewSet):
    """
    유사도 분석 ViewSet

    list: 유사도 분석 목록 조회 (필터링 지원)
    retrieve: 유사도 분석 상세 조회
    create: 유사도 분석 생성
    destroy: 유사도 분석 삭제
    """

    queryset = SimilarityAnalysis.objects.select_related(
        "target_compound", "similar_compound"
    )
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["similarity_score", "analysis_date"]
    ordering = ["-similarity_score"]

    def get_queryset(self):
        """
        쿼리셋 필터링
        """
        queryset = super().get_queryset()

        filter_params = self._build_filter_params()
        queryset = similarity_analysis_service.filter_analyses(
            queryset, filter_params
        )

        return queryset

    def _build_filter_params(self) -> SimilarityFilterParams:
        """쿼리 파라미터를 SimilarityFilterParams로 변환"""
        params = self.request.query_params

        min_score = params.get("min_score")
        max_score = params.get("max_score")
        fingerprint_method = params.get("fingerprint_method")
        is_current = params.get("is_current")
        compound_id = params.get("compound_id")

        return SimilarityFilterParams(
            min_score=float(min_score) if min_score else None,
            max_score=float(max_score) if max_score else None,
            fingerprint_method=fingerprint_method,
            is_current=self._parse_bool(is_current),
            compound_id=int(compound_id) if compound_id else None,
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
            return SimilarityAnalysisListSerializer

        elif self.action == "create":
            return SimilarityAnalysisCreateSerializer

        return SimilarityAnalysisDetailSerializer

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        유사도 분석 통계

        GET /api/analysis/similarities/statistics/
        """
        stats = similarity_analysis_service.get_statistics()
        return Response(asdict(stats))

    @action(detail=False, methods=["get"])
    def by_compound(self, request):
        """
        특정 화합물의 유사 화합물 목록

        GET /api/analysis/similarities/by_compound/?compound_id=1&min_score=0.8

        Query Parameters:
        - compound_id: 화합물 ID (필수)
        - min_score: 최소 유사도 점수 (기본값: 0.7)
        - limit: 결과 수 제한 (기본값: 10)
        """
        compound_id = request.query_params.get("compound_id")

        if not compound_id:
            return Response(
                {"error": "compound_id는 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            compound_id = int(compound_id)
        except ValueError:
            return Response(
                {"error": "compound_id는 숫자여야 합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 화합물 조회
        from apps.compounds.models import Compound
        try:
            compound = Compound.objects.get(id=compound_id)
        except Compound.DoesNotExist:
            return Response(
                {"error": "화합물을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 파라미터 파싱
        try:
            min_score = float(request.query_params.get("min_score", 0.7))
        except ValueError:
            min_score = 0.7

        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10

        similar_compounds = similarity_analysis_service.get_similar_compounds(
            compound, min_score, limit
        )

        return Response({
            "compound_id": compound.id,
            "compound_name": compound.standard_name,
            "min_score": min_score,
            "count": len(similar_compounds),
            "similar_compounds": [asdict(s) for s in similar_compounds],
        })

    @action(detail=False, methods=["post"])
    def invalidate(self, request):
        """
        특정 화합물의 유사도 분석 무효화

        POST /api/analysis/similarities/invalidate/
        Body: {"compound_id": 1}
        """
        compound_id = request.data.get("compound_id")

        if not compound_id:
            return Response(
                {"error": "compound_id는 필수입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            compound_id = int(compound_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "compound_id는 숫자여야 합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        invalidated_count = similarity_analysis_service.invalidate_compound_similarities(
            compound_id
        )

        return Response({
            "compound_id": compound_id,
            "invalidated_count": invalidated_count,
        })
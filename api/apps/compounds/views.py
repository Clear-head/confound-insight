from dataclasses import asdict

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Prefetch, Q

from .models import Compound
from .serializers import (
    CompoundListSerializer,
    CompoundDetailSerializer,
    CompoundCreateSerializer,
    CompoundUpdateSerializer,
    CompoundSearchSerializer,
)
from .services import (
    compound_service,
    CompoundFilterParams,
)


class CompoundViewSet(viewsets.ModelViewSet):
    """
    화합물(Compound) ViewSet

    list: 화합물 목록 조회 (검색/필터링 지원)
    retrieve: 화합물 상세 조회 (관련 제품 포함)
    create: 화합물 생성
    update: 화합물 전체 수정
    partial_update: 화합물 부분 수정
    destroy: 화합물 삭제
    """

    queryset = Compound.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["standard_name", "cid", "molecular_formula", "iupac_name"]
    ordering_fields = ["created_at", "updated_at", "standard_name", "molecular_weight"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        쿼리셋 필터링 및 최적화
        """
        queryset = super().get_queryset()

        # 액션별 쿼리 최적화
        if self.action == "list":
            queryset = queryset.annotate(
                product_count=Count(
                    "products",
                    filter=Q(products__is_main_active=True)
                )
            )

        elif self.action == "retrieve":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "products",
                    queryset=Compound.objects.none()
                )
            )

        # 서비스 레이어를 통한 필터링
        filter_params = self._build_filter_params()
        queryset = compound_service.filter_compounds(queryset, filter_params)

        return queryset

    def _build_filter_params(self) -> CompoundFilterParams:
        """쿼리 파라미터를 CompoundFilterParams로 변환"""
        params = self.request.query_params

        is_valid = params.get("is_valid")
        has_structure = params.get("has_structure")
        has_cid = params.get("has_cid")
        min_weight = params.get("min_weight")
        max_weight = params.get("max_weight")

        return CompoundFilterParams(
            is_valid=self._parse_bool(is_valid),
            has_structure=self._parse_bool(has_structure),
            has_cid=self._parse_bool(has_cid),
            min_weight=float(min_weight) if min_weight else None,
            max_weight=float(max_weight) if max_weight else None,
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
            return CompoundListSerializer

        elif self.action == "create":
            return CompoundCreateSerializer

        elif self.action in ["update", "partial_update"]:
            return CompoundUpdateSerializer

        elif self.action == "search":
            return CompoundSearchSerializer

        return CompoundDetailSerializer

    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        화합물 통계 정보

        GET /api/compounds/statistics/
        """
        stats = compound_service.get_statistics()
        return Response(asdict(stats))

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        화합물 검색

        GET /api/compounds/search/?q=aspirin&type=name

        Query Parameters:
        - q: 검색어 (필수)
        - type: 검색 타입 [name, cid, smiles] (기본값: name)
        """
        query = request.query_params.get("q", "").strip()
        search_type = request.query_params.get("type", "name").lower()

        try:
            results = compound_service.search_compounds(query, search_type)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CompoundSearchSerializer(
            results,
            many=True,
            context={
                "request": request,
                "search_query": query,
                "search_type": search_type,
            }
        )

        return Response({
            "query": query,
            "type": search_type,
            "count": len(serializer.data),
            "results": serializer.data,
        })

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """
        화합물이 포함된 제품 목록

        GET /api/compounds/{id}/products/

        Query Parameters:
        - is_main_active: true/false (주성분만 필터링)
        """
        compound = self.get_object()

        is_main_active = self._parse_bool(
            request.query_params.get("is_main_active")
        )

        products = compound_service.get_compound_products(
            compound, is_main_active
        )

        return Response({
            "compound_id": compound.id,
            "compound_name": compound.standard_name,
            "total_products": len(products),
            "products": [asdict(p) for p in products],
        })

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        """
        유사 화합물 목록 (Tanimoto 유사도 기반)

        GET /api/compounds/{id}/similar/

        Query Parameters:
        - min_score: 최소 유사도 점수 (기본값: 0.7)
        - limit: 결과 수 제한 (기본값: 10)
        """
        compound = self.get_object()

        try:
            min_score = float(request.query_params.get("min_score", 0.7))
        except ValueError:
            min_score = 0.7

        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10

        similar_compounds = compound_service.get_similar_compounds(
            compound, min_score, limit
        )

        return Response({
            "compound_id": compound.id,
            "compound_name": compound.standard_name,
            "min_score": min_score,
            "count": len(similar_compounds),
            "similar_compounds": [asdict(s) for s in similar_compounds],
        })

    def destroy(self, request, *args, **kwargs):
        """
        화합물 삭제

        주의: 관련 ProductIngredient의 compound FK가 NULL로 설정됨
        """
        instance = self.get_object()
        compound_name = instance.standard_name

        self.perform_destroy(instance)

        return Response(
            {"message": f'화합물 "{compound_name}"이(가) 삭제되었습니다.'},
            status=status.HTTP_204_NO_CONTENT
        )
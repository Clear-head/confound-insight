from rest_framework import serializers

from .models import SimilarityAnalysis


class CompoundBriefSerializer(serializers.Serializer):
    """화합물 간략 정보 (순환 import 방지용)"""
    id = serializers.IntegerField()
    standard_name = serializers.CharField()
    cid = serializers.IntegerField(allow_null=True)
    molecular_formula = serializers.CharField(allow_null=True)


class SimilarityAnalysisListSerializer(serializers.ModelSerializer):
    """유사도 분석 목록용 Serializer"""
    target_compound_name = serializers.CharField(
        source="target_compound.standard_name",
        read_only=True
    )
    similar_compound_name = serializers.CharField(
        source="similar_compound.standard_name",
        read_only=True
    )

    class Meta:
        model = SimilarityAnalysis
        fields = [
            "id",
            "target_compound",
            "target_compound_name",
            "similar_compound",
            "similar_compound_name",
            "similarity_score",
            "fingerprint_method",
            "is_current",
            "analysis_date",
        ]


class SimilarityAnalysisDetailSerializer(serializers.ModelSerializer):
    """유사도 분석 상세 Serializer"""
    target_compound = CompoundBriefSerializer(read_only=True)
    similar_compound = CompoundBriefSerializer(read_only=True)

    class Meta:
        model = SimilarityAnalysis
        fields = [
            "id",
            "target_compound",
            "similar_compound",
            "similarity_score",
            "fingerprint_method",
            "similarity_metric",
            "analysis_date",
            "is_current",
        ]


class SimilarityAnalysisCreateSerializer(serializers.ModelSerializer):
    """유사도 분석 생성 Serializer"""

    class Meta:
        model = SimilarityAnalysis
        fields = [
            "target_compound",
            "similar_compound",
            "similarity_score",
            "fingerprint_method",
            "similarity_metric",
        ]

    def validate(self, attrs):
        if attrs["target_compound"] == attrs["similar_compound"]:
            raise serializers.ValidationError(
                "화합물은 자기 자신과 비교할 수 없습니다."
            )
        return attrs
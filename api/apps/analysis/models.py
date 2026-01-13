from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


"""

**책임:**
- 식약처 제품 데이터 수집/저장
- 제품명 기반 검색 API
- 제품-성분 관계 관리
- 정규화 실패 추적

"""


class SimilarityAnalysis(models.Model):
    """화합물 간 Tanimoto 유사도 분석 결과"""

    target_compound = models.ForeignKey(
        'compounds.Compound',
        on_delete=models.CASCADE,
        related_name='similarities_as_target',
        verbose_name=_("대상 화합물")
    )
    similar_compound = models.ForeignKey(
        'compounds.Compound',
        on_delete=models.CASCADE,
        related_name='similarities_as_comparison',
        verbose_name=_("비교 화합물")
    )

    # 유사도 점수 (0.0 ~ 1.0)
    similarity_score = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)
        ],
        db_index=True,
        verbose_name=_("유사도 점수")
    )

    # 계산 메타데이터
    fingerprint_method = models.CharField(
        max_length=50,
        default='Morgan_r2_2048',
        verbose_name=_("지문 방법")
    )
    similarity_metric = models.CharField(
        max_length=50,
        default='Tanimoto',
        verbose_name=_("유사도 지표")
    )

    # 타임스탬프
    analysis_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    # 캐시 유효성
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("최신 결과 여부")
    )

    class Meta:
        app_label = 'analysis'
        db_table = 'compound_similarities'
        verbose_name = _("유사도 분석")
        verbose_name_plural = _("유사도 분석 결과")
        unique_together = ('target_compound', 'similar_compound')
        indexes = [
            models.Index(fields=['target_compound', '-similarity_score']),
            models.Index(fields=['similarity_score', 'is_current']),
            models.Index(fields=['analysis_date']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(target_compound=models.F('similar_compound')),
                name='no_self_similarity',
                violation_error_message='화합물은 자기 자신과 비교할 수 없습니다.'
            )
        ]

    def __str__(self):
        return (
            f"{self.target_compound.standard_name} ↔ "
            f"{self.similar_compound.standard_name}: "
            f"{self.similarity_score:.3f}"
        )
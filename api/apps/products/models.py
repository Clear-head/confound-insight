from django.db import models
from django.utils.translation import gettext_lazy as _

"""

**책임:**
- RDKit 기반 유사도 계산
- Top-N 유사 화합물 조회 API
- 배치 유사도 재계산
- 캐시 무효화 관리

"""


class Product(models.Model):
    """의약품 제품 마스터 정보"""

    product_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("제품명")
    )
    permit_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_("허가번호")
    )
    manufacturer = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("제조사")
    )
    is_combination = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_("복합제 여부")
    )

    # 메타데이터
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 데이터 출처 추적
    source = models.CharField(
        max_length=50,
        default='MFDS',
        verbose_name=_("데이터 출처")
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("최종 동기화 시각")
    )

    class Meta:
        app_label = 'products'
        db_table = 'products'
        verbose_name = _("의약품 제품")
        verbose_name_plural = _("의약품 제품 목록")
        indexes = [
            models.Index(fields=['product_name', 'manufacturer']),
            models.Index(fields=['is_combination', 'created_at']),
        ]

    def __str__(self):
        return f"{self.product_name} ({self.permit_number})"

    def get_active_ingredients(self):
        """주성분만 반환"""
        return self.ingredients.filter(is_main_active=True)


class ProductIngredient(models.Model):
    """제품과 화합물 간 N:M 관계"""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name=_("제품")
    )
    compound = models.ForeignKey(
        'compounds.Compound',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_("화합물")
    )

    # 원본 데이터
    raw_ingredient_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("원본 성분명")
    )
    content = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("함량")
    )
    unit = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("함량 단위")
    )

    # 분류
    is_main_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("주성분 여부")
    )
    ingredient_type = models.CharField(
        max_length=50,
        default='ACTIVE',
        choices=[
            ('ACTIVE', '주성분'),
            ('EXCIPIENT', '첨가제'),
            ('UNKNOWN', '미분류'),
        ],
        verbose_name=_("성분 유형")
    )

    # 정규화 상태 추적
    normalization_status = models.CharField(
        max_length=20,
        default='PENDING',
        choices=[
            ('PENDING', '대기중'),
            ('SUCCESS', '성공'),
            ('FAILED', '실패'),
            ('MANUAL', '수동 매핑'),
        ],
        db_index=True,
        verbose_name=_("정규화 상태")
    )
    normalization_error = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("정규화 오류 메시지")
    )

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'products'
        db_table = 'product_ingredients'
        verbose_name = _("제품-성분 매핑")
        verbose_name_plural = _("제품-성분 매핑 목록")
        unique_together = ('product', 'raw_ingredient_name')
        indexes = [
            models.Index(fields=['normalization_status', 'is_main_active']),
            models.Index(fields=['compound', 'is_main_active']),
        ]

    def __str__(self):
        return f"{self.product.product_name} - {self.raw_ingredient_name}"
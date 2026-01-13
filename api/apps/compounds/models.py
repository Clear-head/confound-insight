from django.db import models
from django.utils.translation import gettext_lazy as _


"""

**책임:**
- PubChem 데이터 수집/저장
- 화합물 구조 검증
- 분자 지문 생성 및 캐싱
- 물성 정보 제공 API

"""


class Compound(models.Model):
    """PubChem 기반 화합물 정보"""

    # 기본 식별자
    standard_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name=_("표준 성분명")
    )
    cid = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("PubChem CID")
    )

    # 구조 정보
    smiles = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Canonical SMILES")
    )
    inchi = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("InChI")
    )
    inchi_key = models.CharField(
        max_length=27,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("InChI Key")
    )

    # 물성 정보
    molecular_formula = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("분자식")
    )
    molecular_weight = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_("분자량")
    )
    iupac_name = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("IUPAC 명칭")
    )

    # 지문(Fingerprint) 캐싱
    fingerprint_morgan = models.BinaryField(
        null=True,
        blank=True,
        verbose_name=_("Morgan Fingerprint")
    )
    fingerprint_type = models.CharField(
        max_length=50,
        default='Morgan_r2_2048',
        verbose_name=_("지문 타입")
    )

    # 데이터 품질 관리
    is_valid = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("유효성 여부")
    )
    validation_error = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("검증 오류 메시지")
    )

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True
    )
    pubchem_last_fetched = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("PubChem 최종 조회 시각")
    )

    class Meta:
        app_label = 'compounds'
        db_table = 'compounds'
        verbose_name = _("화합물")
        verbose_name_plural = _("화합물 목록")
        indexes = [
            models.Index(fields=['is_valid', 'updated_at']),
            models.Index(fields=['molecular_weight']),
        ]

    def __str__(self):
        cid_info = f"CID:{self.cid}" if self.cid else "CID:N/A"
        return f"{self.standard_name} ({cid_info})"

    def has_structure_data(self):
        """구조 분석 가능 여부"""
        return bool(self.smiles and self.fingerprint_morgan)
from django.contrib import admin
from .models import Compound


@admin.register(Compound)
class CompoundAdmin(admin.ModelAdmin):
    list_display = ['standard_name', 'cid', 'molecular_formula', 'molecular_weight', 'is_valid', 'updated_at']
    list_filter = ['is_valid', 'fingerprint_type']
    search_fields = ['standard_name', 'cid', 'molecular_formula']
    readonly_fields = ['created_at', 'updated_at', 'pubchem_last_fetched']

    fieldsets = (
        ('기본 정보', {
            'fields': ('standard_name', 'cid')
        }),
        ('구조 정보', {
            'fields': ('smiles', 'inchi', 'inchi_key', 'fingerprint_type'),
        }),
        ('물성 정보', {
            'fields': ('molecular_formula', 'molecular_weight', 'iupac_name')
        }),
        ('품질 관리', {
            'fields': ('is_valid', 'validation_error'),
        }),
        ('메타데이터', {
            'fields': ('created_at', 'updated_at', 'pubchem_last_fetched'),
            'classes': ('collapse',)
        }),
    )
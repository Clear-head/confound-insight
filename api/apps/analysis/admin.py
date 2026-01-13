from django.contrib import admin
from .models import SimilarityAnalysis


@admin.register(SimilarityAnalysis)
class SimilarityAnalysisAdmin(admin.ModelAdmin):
    list_display = ['target_compound', 'similar_compound', 'similarity_score', 'is_current', 'analysis_date']
    list_filter = ['is_current', 'fingerprint_method', 'similarity_metric']
    search_fields = ['target_compound__standard_name', 'similar_compound__standard_name']
    readonly_fields = ['analysis_date']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('target_compound', 'similar_compound')


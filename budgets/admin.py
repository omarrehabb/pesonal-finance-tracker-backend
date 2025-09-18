from django.contrib import admin
from .models import Budget, BudgetAlert, BudgetTemplate

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'period', 'is_active', 'created_at']
    list_filter = ['period', 'is_active', 'category', 'created_at']
    search_fields = ['user__username', 'category']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'category', 'amount', 'period', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(BudgetAlert)
class BudgetAlertAdmin(admin.ModelAdmin):
    list_display = ['budget', 'alert_type', 'is_read', 'created_at']
    list_filter = ['alert_type', 'is_read', 'created_at']
    search_fields = ['budget__user__username', 'budget__category', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('budget__user')


@admin.register(BudgetTemplate)
class BudgetTemplateAdmin(admin.ModelAdmin):
    list_display = ['category', 'suggested_amount', 'icon', 'color', 'is_active']
    list_filter = ['is_active']
    search_fields = ['category', 'description']
    ordering = ['category']
    
    fieldsets = (
        (None, {
            'fields': ('category', 'suggested_amount', 'description', 'is_active')
        }),
        ('Display', {
            'fields': ('icon', 'color'),
        }),
    )
from rest_framework import serializers
from .models import Budget, BudgetAlert, BudgetTemplate
from decimal import Decimal
from datetime import datetime

class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_over_budget = serializers.SerializerMethodField()
    daily_budget_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'category', 'amount', 'period', 'is_active',
            'created_at', 'updated_at', 'spent', 'remaining', 
            'percentage', 'status', 'days_remaining', 'is_over_budget',
            'daily_budget_remaining'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_spent(self, obj):
        # Get date parameters from context
        context = self.context
        year = context.get('year')
        month = context.get('month')
        week = context.get('week')
        return float(obj.get_spent_amount(year, month, week))
    
    def get_remaining(self, obj):
        context = self.context
        year = context.get('year')
        month = context.get('month')
        week = context.get('week')
        return float(obj.get_remaining_amount(year, month, week))
    
    def get_percentage(self, obj):
        context = self.context
        year = context.get('year')
        month = context.get('month')
        week = context.get('week')
        return round(obj.get_percentage_used(year, month, week), 1)
    
    def get_status(self, obj):
        context = self.context
        year = context.get('year')
        month = context.get('month')
        week = context.get('week')
        return obj.get_status(year, month, week)
    
    def get_days_remaining(self, obj):
        context = self.context
        year = context.get('year')
        month = context.get('month')
        return obj.get_days_remaining(year, month)
    
    def get_is_over_budget(self, obj):
        context = self.context
        year = context.get('year')
        month = context.get('month')
        week = context.get('week')
        return obj.is_over_budget(year, month, week)
    
    def get_daily_budget_remaining(self, obj):
        context = self.context
        year = context.get('year')
        month = context.get('month')
        daily_budget = obj.get_daily_budget_remaining(year, month)
        return float(daily_budget) if daily_budget else None
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        if value > Decimal('1000000.00'):
            raise serializers.ValidationError("Amount cannot exceed $1,000,000")
        return value
    
    def validate_category(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Category is required")
        return value.strip()
    
    def validate(self, data):
        # Check for duplicate budget (same user, category, period)
        user = self.context['request'].user
        category = data.get('category')
        period = data.get('period', 'monthly')
        
        # For updates, exclude current instance
        queryset = Budget.objects.filter(user=user, category=category, period=period)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError({
                'category': f"A budget for {category} ({period}) already exists"
            })
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BudgetSummarySerializer(serializers.Serializer):
    """Serializer for budget summary data"""
    total_budgets = serializers.IntegerField()
    total_budget_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_remaining = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_percentage_used = serializers.FloatField()
    budgets_over_limit = serializers.IntegerField()
    budgets_at_warning = serializers.IntegerField()
    budgets_on_track = serializers.IntegerField()
    period = serializers.CharField()
    year = serializers.IntegerField()
    month = serializers.IntegerField(required=False)
    week = serializers.IntegerField(required=False)


class BudgetAlertSerializer(serializers.ModelSerializer):
    budget_category = serializers.CharField(source='budget.category', read_only=True)
    budget_amount = serializers.DecimalField(source='budget.amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = BudgetAlert
        fields = [
            'id', 'budget', 'budget_category', 'budget_amount',
            'alert_type', 'message', 'is_read', 'created_at'
        ]
        read_only_fields = ['created_at']


class BudgetTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetTemplate
        fields = [
            'id', 'category', 'suggested_amount', 'description',
            'icon', 'color', 'is_active'
        ]


class BudgetRecommendationSerializer(serializers.Serializer):
    """Serializer for budget recommendations based on spending history"""
    category = serializers.CharField()
    recommended_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_spending = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    confidence = serializers.ChoiceField(choices=['low', 'medium', 'high'])
    months_analyzed = serializers.IntegerField()
    transaction_count = serializers.IntegerField()


class CategoryStatsSerializer(serializers.Serializer):
    """Serializer for category spending statistics"""
    category = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = serializers.IntegerField()
    average_transaction = serializers.DecimalField(max_digits=10, decimal_places=2)
    has_budget = serializers.BooleanField()
    budget_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    budget_status = serializers.CharField(required=False)
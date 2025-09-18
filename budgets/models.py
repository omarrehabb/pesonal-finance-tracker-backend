from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime
import calendar

class Budget(models.Model):
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    STATUS_CHOICES = [
        ('good', 'Good'),
        ('caution', 'Caution'),
        ('warning', 'Warning'),
        ('over', 'Over Budget'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=100)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('1000000.00'))]
    )
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='monthly')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'category', 'period']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.category} ({self.period}): ${self.amount}"
    
    def get_spent_amount(self, year=None, month=None, week=None):
        """Calculate spent amount for the current period"""
        from transactions.models import Transaction  # Avoid circular import
        
        # Get current date if not provided
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        
        # Filter transactions based on period
        transactions = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_type='expense',
            date__year=target_year
        )
        
        if self.period == 'monthly':
            transactions = transactions.filter(date__month=target_month)
        elif self.period == 'weekly' and week:
            # Calculate week start and end dates
            import datetime as dt
            week_start = dt.datetime.strptime(f"{target_year}-W{week}-1", "%Y-W%W-%w").date()
            week_end = week_start + dt.timedelta(days=6)
            transactions = transactions.filter(date__range=[week_start, week_end])
        elif self.period == 'yearly':
            # Already filtered by year
            pass
        
        return transactions.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    def get_remaining_amount(self, year=None, month=None, week=None):
        """Calculate remaining budget amount"""
        spent = self.get_spent_amount(year, month, week)
        return self.amount - spent
    
    def get_percentage_used(self, year=None, month=None, week=None):
        """Calculate percentage of budget used"""
        spent = self.get_spent_amount(year, month, week)
        if self.amount == 0:
            return 0
        return min(100, (spent / self.amount) * 100)
    
    def get_status(self, year=None, month=None, week=None):
        """Determine budget status based on usage"""
        percentage = self.get_percentage_used(year, month, week)
        
        if percentage >= 100:
            return 'over'
        elif percentage >= 80:
            return 'warning'
        elif percentage >= 60:
            return 'caution'
        else:
            return 'good'
    
    def is_over_budget(self, year=None, month=None, week=None):
        """Check if budget is exceeded"""
        return self.get_remaining_amount(year, month, week) < 0
    
    def get_days_remaining(self, year=None, month=None):
        """Calculate days remaining in current period"""
        if self.period != 'monthly':
            return None
            
        now = datetime.now()
        target_year = year or now.year
        target_month = month or now.month
        
        # Get last day of the month
        last_day = calendar.monthrange(target_year, target_month)[1]
        
        # Calculate remaining days
        current_day = now.day if (target_year == now.year and target_month == now.month) else 1
        return max(0, last_day - current_day + 1)
    
    def get_daily_budget_remaining(self, year=None, month=None):
        """Calculate daily budget for remaining days"""
        if self.period != 'monthly':
            return None
            
        remaining_amount = self.get_remaining_amount(year, month)
        days_remaining = self.get_days_remaining(year, month)
        
        if days_remaining <= 0:
            return Decimal('0.00')
        
        return remaining_amount / days_remaining if remaining_amount > 0 else Decimal('0.00')


class BudgetAlert(models.Model):
    ALERT_TYPES = [
        ('warning', 'Warning - 80% reached'),
        ('over', 'Over Budget'),
        ('weekly_summary', 'Weekly Summary'),
        ('monthly_summary', 'Monthly Summary'),
    ]
    
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.budget.user.username} - {self.alert_type}: {self.budget.category}"


class BudgetTemplate(models.Model):
    """Predefined budget templates for common categories"""
    category = models.CharField(max_length=100, unique=True)
    suggested_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='📦')  # Emoji icon
    color = models.CharField(max_length=7, default='#9E9E9E')  # Hex color
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category']
    
    def __str__(self):
        return f"{self.category} - ${self.suggested_amount}"
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid

class Bank(models.Model):
    """Represents different banks (Chase, Wells Fargo, etc.)"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # e.g., 'chase', 'wellsfargo'
    logo_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default='#0066CC')  # Hex color
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class BankCustomer(models.Model):
    """Simulates bank customers (for OAuth login simulation)"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)  # In real scenario, this would be hashed
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['bank', 'username']
    
    def __str__(self):
        return f"{self.full_name} ({self.bank.name})"

class BankAccount(models.Model):
    """Bank accounts for each customer"""
    ACCOUNT_TYPES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
        ('credit', 'Credit Card'),
    ]
    
    customer = models.ForeignKey(BankCustomer, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_name = models.CharField(max_length=100)  # e.g., "Primary Checking"
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.account_name} ({self.account_number})"

class BankTransaction(models.Model):
    """Transactions for bank accounts"""
    TRANSACTION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]
    
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    merchant = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, blank=True)
    date = models.DateTimeField()
    posted_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.account.account_name} - {self.description} (${self.amount})"

class ConnectedAccount(models.Model):
    """Links user's finance app account to bank accounts"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=100)
    refresh_token = models.CharField(max_length=100, blank=True)
    expires_at = models.DateTimeField()
    connected_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'bank_account']
    
    def __str__(self):
        return f"{self.user.username} -> {self.bank_account}"

class ImportedTransaction(models.Model):
    """Tracks which bank transactions have been imported"""
    connected_account = models.ForeignKey(ConnectedAccount, on_delete=models.CASCADE)
    bank_transaction = models.ForeignKey(BankTransaction, on_delete=models.CASCADE)
    finance_transaction = models.ForeignKey('transactions.Transaction', on_delete=models.CASCADE)
    imported_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['connected_account', 'bank_transaction']
    
    def __str__(self):
        return f"Imported: {self.bank_transaction.description}"
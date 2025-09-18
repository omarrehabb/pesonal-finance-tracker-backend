from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )


    # Relates the transaction to the user who created it
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    # Income or expense
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Category of income or expense
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    # Allow client to provide a specific datetime; default to now
    date = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        # Get the user's profile to update the balance
        user_profile = self.user.userprofile

        # Adjust balance based on transaction type
        if self.transaction_type == 'income':
            user_profile.balance += self.amount
        elif self.transaction_type == 'expense':
            user_profile.balance -= self.amount

        user_profile.save()
        super(Transaction, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}: {self.transaction_type.capitalize()} of {self.amount}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.user.username} - Balance: {self.balance}'

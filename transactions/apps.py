from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transactions'

    def ready(self) -> None:
        import transactions.signals
        return super().ready()

# Fix signal to create UserProfile when new User is created.

        

"""
Management command to recalculate all user balances based on their order history.
This is useful for data consistency checks or migration from legacy systems.

Usage:
    python manage.py recalculate_balances
    python manage.py recalculate_balances --user-id 123  # Single user
    python manage.py recalculate_balances --dry-run      # Preview changes
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal
from order.models import GiftCardOrder
from withdrawal.models import Withdrawal

User = get_user_model()


class Command(BaseCommand):
    help = 'Recalculate all user balances based on their order history'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Recalculate balances for a specific user ID only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        user_id = options['user_id']
        dry_run = options['dry_run']

        if user_id:
            users = User.objects.filter(id=user_id)
            if not users.exists():
                raise CommandError(f'User with ID {user_id} not found')
        else:
            users = User.objects.all()

        total_users = users.count()
        updated_count = 0
        changes = []

        self.stdout.write(f'Recalculating balances for {total_users} user(s)...')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be saved'))
        self.stdout.write('')

        for user in users:
            # Calculate pending balance (orders with status 'Pending' or 'Processing')
            pending_result = GiftCardOrder.objects.filter(
                user=user,
                status__in=['Pending', 'Processing']
            ).aggregate(total=Sum('amount'))
            pending_balance = pending_result['total'] or Decimal('0.00')

            # Calculate gross withdrawable balance from approved/completed orders
            withdrawable_result = GiftCardOrder.objects.filter(
                user=user,
                status__in=['Approved', 'Completed']
            ).aggregate(total=Sum('amount'))
            gross_withdrawable_balance = withdrawable_result['total'] or Decimal('0.00')

            # Reserve funds for active/completed withdrawals.
            reserved_withdrawals_result = Withdrawal.objects.filter(
                user=user,
                status__in=['Pending', 'Processing', 'Approved', 'Completed'],
            ).aggregate(total=Sum('amount'))
            reserved_withdrawals_total = reserved_withdrawals_result['total'] or Decimal('0.00')

            withdrawable_balance = max(
                Decimal('0.00'),
                gross_withdrawable_balance - reserved_withdrawals_total
            )

            # Check if balances have changed
            old_pending = user.pending_balance
            old_withdrawable = user.withdrawable_balance

            pending_changed = pending_balance != old_pending
            withdrawable_changed = withdrawable_balance != old_withdrawable

            if pending_changed or withdrawable_changed:
                updated_count += 1
                change_info = {
                    'user': user,
                    'old_pending': old_pending,
                    'new_pending': pending_balance,
                    'old_withdrawable': old_withdrawable,
                    'new_withdrawable': withdrawable_balance,
                }
                changes.append(change_info)

                if not dry_run:
                    user.pending_balance = pending_balance
                    user.withdrawable_balance = withdrawable_balance
                    user.save()

                # Display change
                self.stdout.write(f'User: {user.email} (ID: {user.id})')
                if pending_changed:
                    self.stdout.write(
                        f'  Pending: {old_pending} → {pending_balance}',
                        style='WARNING' if pending_balance > old_pending else ''
                    )
                if withdrawable_changed:
                    self.stdout.write(
                        f'  Withdrawable: {old_withdrawable} → {withdrawable_balance}',
                        style='WARNING' if withdrawable_balance > old_withdrawable else ''
                    )
                self.stdout.write('')

        # Summary
        self.stdout.write('=' * 50)
        self.stdout.write(f'Summary:')
        self.stdout.write(f'  Total users processed: {total_users}')
        self.stdout.write(f'  Users with balance changes: {updated_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN completed. No changes were saved.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {updated_count} user(s).'))

        # Show total balances
        total_pending = User.objects.aggregate(total=Sum('pending_balance'))['total'] or Decimal('0.00')
        total_withdrawable = User.objects.aggregate(total=Sum('withdrawable_balance'))['total'] or Decimal('0.00')
        
        self.stdout.write(f'\nTotal System Balances:')
        self.stdout.write(f'  Total Pending: ${total_pending:,.2f}')
        self.stdout.write(f'  Total Withdrawable: ${total_withdrawable:,.2f}')

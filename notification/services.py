"""
Notification Service - Event-driven notification system.
Handles both email and in-app notifications.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string, get_template
from django.conf import settings
from django.utils import timezone
from django.db import transaction

if TYPE_CHECKING:
    from account.models import UserProfile

from .models import Notification, NotificationEvent


class NotificationService:
    """
    Central notification service for handling all user notifications.
    Uses event-driven architecture for decoupled notification dispatch.
    """

    @staticmethod
    def send_notification(
        user: 'UserProfile',
        notification_type: str,
        title: str,
        message: str,
        priority: str = 'medium',
        send_email: bool = True,
        object_id: Optional[int] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[Optional[Notification], Optional[NotificationEvent]]:
        """
        Send a notification to a user via in-app and/or email.

        Args:
            user: The recipient user
            notification_type: Type of notification (e.g., 'order_approved')
            title: Notification title
            message: Notification message body
            priority: Priority level (low, medium, high, urgent)
            send_email: Whether to also send email notification
            object_id: Optional related object ID
            content_type: Optional content type (e.g., 'order', 'withdrawal')
            metadata: Optional additional metadata

        Returns:
            Tuple of (Notification, NotificationEvent) or (None, None) on failure
        """
        notification = None
        event = None

        try:
            with transaction.atomic():
                # Create in-app notification
                notification = Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    object_id=object_id,
                    content_type=content_type,
                )

                # Create event log entry
                channel = 'both' if send_email else 'in_app'
                event = NotificationEvent.objects.create(
                    user=user,
                    event_type=notification_type,
                    title=title,
                    message=message,
                    channel=channel,
                    status='pending',
                    metadata=metadata or {},
                )

            # Send email asynchronously (outside atomic block)
            if send_email:
                sent, error_message = EmailNotificationSender.send(
                    user=user,
                    subject=title,
                    template_name=f'notification/{notification_type}_email.html',
                    context={
                        'user': user,
                        'message': message,
                        'notification': notification,
                        **(metadata or {}),
                    }
                )
                if sent:
                    event.status = 'sent'
                    event.sent_at = timezone.now()
                    event.save(update_fields=['status', 'sent_at'])
                else:
                    event.status = 'failed'
                    event.error_message = error_message or 'Unknown email delivery error'
                    event.save(update_fields=['status', 'error_message'])
            else:
                event.status = 'sent'
                event.sent_at = timezone.now()
                event.save(update_fields=['status', 'sent_at'])

            return notification, event

        except Exception as e:
            # Log error but don't raise - notification failure shouldn't break main flow
            print(f"Notification service error: {e}")
            return None, None

    @staticmethod
    def get_unread_count(user: 'UserProfile') -> int:
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(user=user, is_read=False).count()

    @staticmethod
    def get_notifications(
        user: 'UserProfile',
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user."""
        queryset = Notification.objects.filter(user=user)
        if unread_only:
            queryset = queryset.filter(is_read=False)
        return queryset[:limit]

    @staticmethod
    def mark_all_as_read(user: 'UserProfile') -> int:
        """Mark all notifications as read for a user."""
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())


class EmailNotificationSender:
    """Handles sending email notifications."""

    @staticmethod
    def send(
        user: 'UserProfile',
        subject: str,
        template_name: str,
        context: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """
        Send an email notification.

        Args:
            user: Recipient user
            subject: Email subject
            template_name: Path to email template
            context: Template context

        Returns:
            Tuple of (success, error_message)
        """
        try:
            from_email = getattr(settings, 'EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
            to_email = user.email

            html_template, text_template = EmailNotificationSender.resolve_templates(template_name)

            if not html_template or not text_template:
                return False, f'No templates found for {template_name}'

            text_content = render_to_string(text_template, context)
            html_content = render_to_string(html_template, context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email],
            )
            email.attach_alternative(html_content, 'text/html')
            email.send()

            return True, None
        except Exception as e:
            print(f"Email send error: {e}")
            return False, str(e)

    @staticmethod
    def resolve_templates(template_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve notification templates:
        1) specific template for notification type
        2) fallback generic notification template
        """
        candidates = [template_name, 'notification/general_email.html']
        for html_template in candidates:
            text_template = html_template.replace('.html', '.txt')
            try:
                get_template(html_template)
                get_template(text_template)
                return html_template, text_template
            except TemplateDoesNotExist:
                continue
        return None, None


# Convenience functions for common notification types
def notify_order_created(user: 'UserProfile', order: Any, amount: float) -> None:
    """Send notification when an order is created."""
    NotificationService.send_notification(
        user=user,
        notification_type='order_created',
        title='Order Received',
        message=f'Your gift card order for ₦{amount} has been received and is being processed.',
        priority='medium',
        object_id=order.id,
        content_type='order',
        metadata={'order_id': order.id, 'amount': amount},
    )


def notify_order_status_changed(
    user: 'UserProfile',
    order: Any,
    new_status: str,
    amount: float,
) -> None:
    """Send notification when order status changes."""
    status_messages = {
        'Pending': ('Order Received', f'Your gift card order for ₦{amount} is pending review.'),
        'Approved': ('Order Approved', f'Your gift card order for ₦{amount} has been approved. The amount is now available in your withdrawable balance.'),
        'Rejected': ('Order Rejected', f'Your gift card order for ₦{amount} has been rejected. Please contact support for more information.'),
        'Processing': ('Order Being Processed', f'Your gift card order for ₦{amount} is being processed by our team.'),
        'Assigned': ('Order Being Processed', f'Your gift card order for ₦{amount} is being processed by our team.'),
        'Completed': ('Order Completed', f'Your gift card order for ₦{amount} has been completed. The amount is now available in your withdrawable balance.'),
        'Cancelled': ('Order Cancelled', f'Your gift card order for ₦{amount} has been cancelled.'),
    }

    title, message = status_messages.get(new_status, ('Order Update', f'Your order status has been updated to {new_status}.'))

    notification_type_map = {
        'Pending': 'order_created',
        'Approved': 'order_approved',
        'Rejected': 'order_rejected',
        'Processing': 'order_assigned',
        'Assigned': 'order_assigned',
        'Completed': 'order_completed',
        'Cancelled': 'general',
    }

    NotificationService.send_notification(
        user=user,
        notification_type=notification_type_map.get(new_status, 'general'),
        title=title,
        message=message,
        priority='high' if new_status in ['Approved', 'Rejected', 'Completed'] else 'medium',
        object_id=order.id,
        content_type='order',
        metadata={'order_id': order.id, 'amount': amount, 'status': new_status},
    )


def notify_withdrawal_status_changed(
    user: 'UserProfile',
    withdrawal: Any,
    new_status: str,
    amount: float,
    reason: Optional[str] = None,
    transaction_reference: Optional[str] = None,
) -> None:
    """Send notification when withdrawal status changes."""
    if new_status == 'Approved':
        title = 'Withdrawal Approved'
        message = f'Your withdrawal request for ₦{amount} has been approved and processed.'
    elif new_status == 'Rejected':
        title = 'Withdrawal Rejected'
        message = f'Your withdrawal request for ₦{amount} has been rejected. Please contact support for more information.'
    else:
        return

    NotificationService.send_notification(
        user=user,
        notification_type=f'withdrawal_{new_status.lower()}',
        title=title,
        message=message,
        priority='urgent',
        object_id=withdrawal.id,
        content_type='withdrawal',
        metadata={
            'withdrawal_id': withdrawal.id,
            'amount': amount,
            'status': new_status,
            'reason': reason,
            'transaction_reference': transaction_reference,
        },
    )


def notify_withdrawal_created(
    user: 'UserProfile',
    withdrawal: Any,
    amount: float,
) -> None:
    """Send notification when a withdrawal request is created."""
    NotificationService.send_notification(
        user=user,
        notification_type='withdrawal_created',
        title='Withdrawal Requested',
        message=f'Your withdrawal request for ₦{amount} has been received and is pending review.',
        priority='medium',
        object_id=withdrawal.id,
        content_type='withdrawal',
        metadata={'withdrawal_id': withdrawal.id, 'amount': amount, 'status': 'Pending'},
    )


def notify_kyc_status_changed(
    user: 'UserProfile',
    level: str,
    new_status: str,
) -> None:
    """Send notification when KYC credentials status changes."""
    if new_status == 'Approved':
        title = f'Level {level} Verification Approved'
        message = f'Congratulations! Your Level {level} verification has been approved. Your transaction limit has been updated.'
    else:
        title = f'Level {level} Verification Rejected'
        message = f'Your Level {level} verification documents have been rejected. Please resubmit with correct information.'

    NotificationService.send_notification(
        user=user,
        notification_type=f'kyc_{new_status.lower()}',
        title=title,
        message=message,
        priority='high',
        content_type='kyc',
        metadata={'level': level, 'status': new_status},
    )


def notify_balance_updated(
    user: 'UserProfile',
    balance_type: str,
    new_balance: float,
    change_amount: Optional[float] = None,
) -> None:
    """Send notification when user balance is updated."""
    balance_names = {
        'pending': 'Pending Balance',
        'withdrawable': 'Withdrawable Balance',
    }

    if change_amount:
        message = f'Your {balance_names.get(balance_type, balance_type)} has been updated. New balance: ₦{new_balance:,.2f} (Change: ₦{change_amount:,.2f})'
    else:
        message = f'Your {balance_names.get(balance_type, balance_type)} has been updated. New balance: ₦{new_balance:,.2f}'

    NotificationService.send_notification(
        user=user,
        notification_type='balance_updated',
        title='Balance Updated',
        message=message,
        priority='medium',
        content_type='balance',
        metadata={'balance_type': balance_type, 'new_balance': new_balance, 'change_amount': change_amount},
    )

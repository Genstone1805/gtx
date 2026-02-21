# GTX Gift Card Redemption System - API Documentation

## Overview

This document describes the refactored gift card redemption system with:
- Event-driven notification system (email + in-app)
- User balance tracking (pending and withdrawable)
- Withdrawal management system

---

## Table of Contents

1. [User Balance Endpoints](#user-balance-endpoints)
2. [Withdrawal Endpoints](#withdrawal-endpoints)
3. [Notification Endpoints](#notification-endpoints)
4. [Order Management Endpoints](#order-management-endpoints)
5. [Admin Endpoints](#admin-endpoints)

---

## User Balance Endpoints

### Get User Profile with Balances
```
GET /account/me/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "pending_balance": "150000.00",
  "withdrawable_balance": "500000.00",
  "level": "Level 2",
  "transaction_limit": "5000000.00",
  ...
}
```

### Get Balance Summary
```
GET /withdrawal/balance/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "pending_balance": "150000.00",
  "withdrawable_balance": "500000.00",
  "transaction_limit": "5000000.00",
  "total_balance": "650000.00"
}
```

---

## Withdrawal Endpoints

### Create Withdrawal Request
```
POST /withdrawal/requests/create/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": "50000.00",
  "payment_method": "bank_transfer",
  "bank_name": "First Bank",
  "account_name": "John Doe",
  "account_number": "1234567890",
  "transaction_pin": "1234"
}
```

**Payment Method Options:**
- `bank_transfer` - Requires: bank_name, account_name, account_number
- `mobile_money` - Requires: mobile_money_number, mobile_money_provider
- `crypto` - Requires: crypto_address, crypto_network

**Response:**
```json
{
  "detail": "Withdrawal request created successfully.",
  "withdrawal_id": 1,
  "amount": "50000.00",
  "status": "Pending"
}
```

### List User Withdrawals
```
GET /withdrawal/requests/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "amount": "50000.00",
    "payment_method": "bank_transfer",
    "payment_method_display": "Bank Transfer",
    "status": "Pending",
    "status_display": "Pending",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Withdrawal Detail
```
GET /withdrawal/requests/<id>/
Authorization: Bearer <token>
```

### Cancel Withdrawal
```
POST /withdrawal/requests/<id>/cancel/
Authorization: Bearer <token>
```

**Note:** Only pending withdrawals can be cancelled.

---

## Notification Endpoints

### List Notifications
```
GET /notifications/
Authorization: Bearer <token>
```

**Query Parameters:**
- `unread_only=true` - Filter unread notifications only
- `type=order_approved` - Filter by notification type

**Response:**
```json
[
  {
    "id": 1,
    "notification_type": "order_approved",
    "notification_type_display": "Order Approved",
    "title": "Order Approved",
    "message": "Your gift card order for $50000 has been approved...",
    "priority": "high",
    "priority_display": "High",
    "is_read": false,
    "created_at": "2024-01-15T10:30:00Z",
    "created_at_formatted": "2024-01-15 10:30",
    "read_at": null
  }
]
```

### Get Notification Detail
```
GET /notifications/<id>/
Authorization: Bearer <token>
```

### Mark Notifications as Read
```
POST /notifications/mark-as-read/
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "ids": [1, 2, 3]  // Optional - if empty, marks all as read
}
```

### Get Unread Count
```
GET /notifications/unread-count/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "unread_count": 5
}
```

---

## Order Management Endpoints

### Create Gift Card Order
```
POST /order/create/
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Fields:**
- `type` - "Physical" or "E-Code"
- `card` - Gift card ID
- `amount` - Order amount
- `image` - Required for Physical type
- `e_code_pin` - Required for E-Code type

### List User Orders
```
GET /account/transactions/
Authorization: Bearer <token>
```

### Get Order Detail
```
GET /account/transactions/<id>/
Authorization: Bearer <token>
```

---

## Admin Endpoints

### Admin: List All Withdrawals
```
GET /withdrawal/admin/requests/
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status=Pending` - Filter by status
- `user_id=1` - Filter by user

### Admin: Get Withdrawal Detail
```
GET /withdrawal/admin/requests/<id>/
Authorization: Bearer <admin_token>
```

### Admin: Process Withdrawal (Approve/Reject)
```
POST /withdrawal/admin/requests/<id>/process/
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request Body (Approve):**
```json
{
  "action": "approve",
  "transaction_reference": "TXN123456",
  "admin_notes": "Processed via bank transfer"
}
```

**Request Body (Reject):**
```json
{
  "action": "reject",
  "reason": "Invalid account number provided",
  "admin_notes": "Contacted user for correction"
}
```

**Response (Approve):**
```json
{
  "detail": "Withdrawal approved successfully. Amount $50000.00 has been deducted from user's withdrawable balance.",
  "status": "Approved",
  "transaction_reference": "TXN123456"
}
```

### Admin: Get Withdrawal Audit Log
```
GET /withdrawal/admin/requests/<withdrawal_id>/audit-log/
Authorization: Bearer <admin_token>
```

### Admin: Pending Withdrawals Count
```
GET /withdrawal/admin/pending-count/
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "pending_count": 5,
  "pending_total": "250000.00"
}
```

### Admin: Update Order Status
```
PATCH /admin/update-order-status/<order_id>/
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "Approved",
  "admin_notes": "Verified and approved"
}
```

**Available Statuses:**
- `Processing`
- `Assigned`
- `Approved`
- `Rejected`
- `Completed`
- `Cancelled`

### Admin: List Pending Orders
```
GET /admin/pending-orders/
Authorization: Bearer <admin_token>
```

### Admin: Notification Events (Audit)
```
GET /notifications/admin/events/
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `status=sent` - Filter by event status
- `user_id=1` - Filter by user
- `channel=email` - Filter by channel

### Admin: Notification Statistics
```
GET /notifications/admin/stats/
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "total_notifications": 150,
  "unread_notifications": 25,
  "total_events": 145,
  "sent_events": 140,
  "failed_events": 5,
  "success_rate": "96.55%",
  "notifications_by_type": [
    {"notification_type": "order_approved", "count": 50},
    {"notification_type": "order_created", "count": 45},
    ...
  ]
}
```

---

## Balance Flow Diagram

```
User Creates Order (Amount: $1000)
         │
         ▼
   Order Status: Processing
   pending_balance: +$1000
   withdrawable_balance: $0
         │
         ▼
   Admin Approves Order
         │
         ▼
   Order Status: Approved
   pending_balance: $0
   withdrawable_balance: +$1000
         │
         ▼
   User Requests Withdrawal ($500)
         │
         ▼
   Withdrawal Status: Pending
   withdrawable_balance: $1000 (unchanged)
         │
         ▼
   Admin Approves Withdrawal
         │
         ▼
   Withdrawal Status: Approved
   withdrawable_balance: $500 (deducted)
```

---

## Notification Types

| Type | Trigger | Priority |
|------|---------|----------|
| `order_created` | User creates order | medium |
| `order_approved` | Admin approves order | high |
| `order_rejected` | Admin rejects order | high |
| `order_assigned` | Order assigned for review | medium |
| `order_completed` | Order completed | medium |
| `withdrawal_created` | User requests withdrawal | medium |
| `withdrawal_approved` | Admin approves withdrawal | urgent |
| `withdrawal_rejected` | Admin rejects withdrawal | urgent |
| `kyc_approved` | KYC credentials approved | high |
| `kyc_rejected` | KYC credentials rejected | high |
| `balance_updated` | Balance changes | medium |

---

## Management Commands

### Recalculate User Balances

Recalculates all user balances based on order history.

```bash
# Recalculate all users
python manage.py recalculate_balances

# Recalculate specific user
python manage.py recalculate_balances --user-id 123

# Preview changes without saving
python manage.py recalculate_balances --dry-run
```

---

## Error Responses

### Insufficient Balance
```json
{
  "amount": [
    "Insufficient withdrawable balance. Your current withdrawable balance is $100000.00."
  ]
}
```

### Missing Transaction PIN
```json
{
  "detail": "You must create a transaction PIN before making withdrawals."
}
```

### Invalid Transaction PIN
```json
{
  "transaction_pin": "Incorrect transaction PIN."
}
```

### Cannot Cancel Withdrawal
```json
{
  "detail": "Cannot cancel withdrawal with status: Approved"
}
```

---

## Security Features

1. **Transaction PIN** - Required for all withdrawal requests
2. **Balance Lock** - Withdrawable balance is locked during pending withdrawal
3. **Audit Logging** - All withdrawal actions are logged
4. **Email Notifications** - Users notified of all balance changes
5. **Admin Approval** - All withdrawals require admin approval

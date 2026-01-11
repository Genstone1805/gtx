# GTX - Gift Card Trading Platform

A Django REST API backend for a gift card trading and management platform with multi-level identity verification (KYC), JWT authentication, and admin controls.

---

## Table of Contents

- [Project Objective](#project-objective)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Models](#database-models)
  - [Account App](#account-app)
  - [Cards App](#cards-app)
  - [Order App](#order-app)
- [API Endpoints](#api-endpoints)
- [Authentication Flow](#authentication-flow)
- [KYC Verification Levels](#kyc-verification-levels)
- [Installation](#installation)
- [Configuration](#configuration)

---

## Project Objective

GTX is designed to:

- Enable users to buy, sell, and manage gift cards
- Implement a tiered identity verification system (Level 1, Level 2, Level 3)
- Provide secure user authentication with email verification
- Manage gift card inventories for multiple retailers/stores
- Process gift card orders (physical and e-code types)
- Enforce transaction limits based on user verification level
- Provide admin controls for credential approval and gift card management

---

## Features

- **User Authentication**: JWT-based authentication with email verification
- **Multi-Level KYC**: Three-tier identity verification (NIN, address, face verification)
- **Transaction Security**: 4-digit transaction PIN for additional security
- **Gift Card Catalog**: Store and manage gift cards from multiple retailers
- **Admin Panel**: Approve/reject user credentials and manage gift card inventory
- **Email Notifications**: Automated emails for verification, password reset, and login alerts

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 6.0 | Backend Framework |
| Django REST Framework | 3.16.1 | API Framework |
| djangorestframework_simplejwt | 5.5.1 | JWT Authentication |
| phonenumber_field | 8.4.0 | Phone Number Validation |
| whitenoise | 6.11.0 | Static File Serving |
| django-cors-headers | 4.9.0 | CORS Support |
| Pillow | 12.0.0 | Image Processing |
| SQLite3 / PostgreSQL | - | Database |

---

## Project Structure

```
gtx/
├── account/           # User authentication, profile, and KYC
├── cards/             # Gift card store and catalog management
├── control/           # Admin control panel
├── order/             # Gift card order processing
├── gtx/               # Project configuration
├── frontend/          # Frontend application
├── media/             # User uploads
├── staticfiles/       # Static files
├── manage.py
└── requirements.txt
```

---

## Database Models

### Account App

#### UserProfile

Custom user model extending `AbstractBaseUser` and `PermissionsMixin`.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `email` | EmailField | `unique=True` | Primary login identifier |
| `is_active` | BooleanField | `default=True` | Account active status |
| `is_staff` | BooleanField | `default=False` | Admin panel access |
| `is_verified` | BooleanField | `default=False` | Email verification status |
| `date_joined` | DateTimeField | `default=timezone.now` | Registration timestamp |
| `last_login` | DateTimeField | `null=True, blank=True` | Last login timestamp |
| `dp` | ImageField | `blank=True` | Profile picture |
| `full_name` | CharField | `max_length=80, blank=True` | User's full name |
| `phone_number` | PhoneNumberField | `unique=True, blank=True, null=True` | International phone number |
| `created_at` | DateTimeField | `auto_now_add=True` | Account creation timestamp |
| `ip_address` | GenericIPAddressField | `null=True, blank=True` | Last login IP address |
| `status` | CharField | `max_length=12, default='Active'` | Account status |
| `disabled` | BooleanField | `default=False` | Account disabled flag |
| `level` | CharField | `max_length=12, default='Level 1'` | KYC verification level |
| `transaction_pin` | CharField | `max_length=4, blank=True` | 4-digit transaction PIN |
| `has_pin` | BooleanField | `default=False` | PIN creation indicator |
| `transaction_limit` | DecimalField | `max_digits=12, decimal_places=2, default=250000.00` | Transaction limit |
| `level2_credentials` | ForeignKey | `on_delete=SET_NULL, null=True, blank=True` | Reference to Level2Credentials |
| `level3_credentials` | ForeignKey | `on_delete=SET_NULL, null=True, blank=True` | Reference to Level3Credentials |

**Status Choices**: `Active`, `Warning`, `Disabled`, `Under Review`

**Level Choices**: `Level 1`, `Level 2`, `Level 3`

---

#### Level2Credentials

NIN (National Identification Number) verification for Level 2.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `nin` | CharField | `max_length=12, blank=True, unique=True` | National ID Number |
| `nin_image` | ImageField | Required | Image of NIN document |
| `status` | CharField | `max_length=12, default='Pending'` | Approval status |
| `approved` | BooleanField | `default=False` | Approval flag |

**Status Choices**: `Pending`, `Approved`, `Rejected`

---

#### Level3Credentials

Address and face verification for Level 3.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `house_address_1` | CharField | `max_length=100` | Primary address |
| `house_address_2` | CharField | `max_length=100, blank=True` | Secondary address |
| `nearest_bus_stop` | TextField | `max_length=60` | Nearest bus stop |
| `city` | TextField | `max_length=50` | City name |
| `state` | CharField | `max_length=50` | State/Province |
| `country` | CharField | `max_length=50` | Country name |
| `proof_of_address_image` | ImageField | Required | Utility bill or address proof |
| `face_verification_image` | ImageField | Required | Selfie for biometric verification |
| `status` | CharField | `max_length=12, default='Pending'` | Approval status |
| `approved` | BooleanField | `default=False` | Approval flag |

**Status Choices**: `Pending`, `Approved`, `Rejected`

---

#### EmailVerificationCode

Email verification codes for account activation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user` | ForeignKey | `on_delete=CASCADE, related_name='verification_codes'` | Associated user |
| `code` | CharField | `max_length=6` | 6-digit verification code |
| `created_at` | DateTimeField | `auto_now_add=True` | Creation timestamp |

**Expiration**: 10 minutes

---

#### PasswordResetCode

Password reset verification codes.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user` | ForeignKey | `on_delete=CASCADE, related_name='password_reset_codes'` | Associated user |
| `code` | CharField | `max_length=6` | 6-digit reset code |
| `created_at` | DateTimeField | `auto_now_add=True` | Creation timestamp |

**Expiration**: 10 minutes

---

### Cards App

#### GiftCardStore

Retailer/brand information for gift cards.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `category` | CharField | `max_length=50, default='All'` | Store category |
| `name` | CharField | `max_length=50, unique=True` | Store name (e.g., Amazon, iTunes) |
| `image` | ImageField | `upload_to='gift stores', null=True` | Store logo/image |
| `user` | ForeignKey | `on_delete=CASCADE, null=True` | Store creator |

**Category Choices**: `All`, `Popular`, `Shopping`

---

#### GiftCardNames

Specific gift card products within a store.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `type` | CharField | `max_length=50, default='Both'` | Card delivery type |
| `name` | CharField | `max_length=150` | Card name/description |
| `store` | ForeignKey | `on_delete=CASCADE` | Parent store |
| `user` | ForeignKey | `on_delete=CASCADE, null=True` | Card creator |
| `rate` | DecimalField | `max_digits=6, decimal_places=2, default=0.00` | Exchange/commission rate |

**Type Choices**: `Both`, `Physical`, `E-code`

---

### Order App

#### GiftCardOrder

Gift card purchase orders.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `user` | ForeignKey | `on_delete=CASCADE` | Buyer |
| `type` | CharField | `max_length=50` | Delivery type |
| `name` | ForeignKey | `on_delete=SET_NULL, null=True` | Gift card product |
| `image` | ImageField | Required | Card image |
| `amount` | IntegerField | Required | Order quantity/amount |
| `status` | CharField | `max_length=50` | Order status |

**Type Choices**: `Physical`, `E-Code`

**Status Choices**: `Processing`, `Rejected`, `Approved`

---

## API Endpoints

### Account Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/account/signup/` | POST | No | Register new user |
| `/account/signup/verify/` | POST | No | Verify email with 6-digit code |
| `/account/signup/resend-code/` | POST | No | Resend verification code |
| `/account/login/` | POST | No | Login and receive JWT tokens |
| `/api/account/token/refresh/` | POST | No | Refresh access token |
| `/account/change-password/` | POST | Yes | Change password |
| `/account/password/reset/` | POST | No | Request password reset |
| `/account/password/reset/verify/` | POST | No | Verify reset code |
| `/account/pin/create/` | POST | Yes | Create transaction PIN |
| `/account/pin/update/` | POST | Yes | Update transaction PIN |
| `/account/credentials/level2/` | POST | Yes | Submit Level 2 credentials |
| `/account/credentials/level3/` | POST | Yes | Submit Level 3 credentials |
| `/account/me/` | GET | Yes | Get user profile |
| `/account/profile/picture/upload/` | POST | Yes | Upload profile picture |
| `/account/profile/picture/update/` | POST | Yes | Update profile picture |
| `/account/profile/phone/add/` | POST | Yes | Add phone number to profile |

### Cards Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/cards/gift-card-stores/` | GET | No | List all gift card stores with cards |

### Admin Control Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/admin/create-gift-store/` | POST | Admin | Create gift card store |
| `/admin/create-gift-card/` | POST | Admin | Create gift card |
| `/admin/list-gift-stores/` | GET | Admin | List all stores |
| `/admin/list-gift-cards/` | GET | Admin | List all gift cards |
| `/admin/get-gift-card/<id>/` | GET/PUT/DELETE | Admin | Manage specific card |
| `/admin/get-gift-store/<id>/` | GET/PUT/DELETE | Admin | Manage specific store |
| `/admin/pending/level2/` | GET | Admin | List pending Level 2 credentials |
| `/admin/pending/level3/` | GET | Admin | List pending Level 3 credentials |
| `/admin/approve/level2/<id>/` | POST | Admin | Approve/reject Level 2 |
| `/admin/approve/level3/<id>/` | POST | Admin | Approve/reject Level 3 |

---

## Authentication Flow

1. User registers with email and password
2. System sends 6-digit verification code via email
3. User verifies email with code
4. User logs in and receives JWT tokens
5. Access token valid for **1 day**
6. Refresh token valid for **7 days** (with rotation)

---

## KYC Verification Levels

| Level | Requirements | Transaction Limit |
|-------|--------------|-------------------|
| Level 1 | Email verification | 250,000 |
| Level 2 | NIN verification (admin approval required) | 5,000,000 |
| Level 3 | Address + Face verification (admin approval required) | 50,000,000 |

---

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gtx
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (True/False) |
| `DATABASE_URL` | PostgreSQL connection string |
| `EMAIL_HOST_USER` | Gmail email address |
| `EMAIL_HOST_PASSWORD` | Gmail app password |

### JWT Settings

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## License

This project is proprietary software.

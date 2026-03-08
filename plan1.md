# Backend Implementation Plan — Multi-Tenant Marketplace

> **Generated from**: Analysis of all 7 frontend HTML templates  
> **Target file for models**: `base/models.py`  
> **Constraint**: HTML files remain untouched (backend adapts to existing frontend)

---

## Table of Contents

1. [Frontend Templates Summary](#1-frontend-templates-summary)
2. [Models to Add in `base/models.py`](#2-models-to-add-in-basemodelspy)
3. [Backend Functionalities (Ranked by Priority)](#3-backend-functionalities-ranked-by-priority)
4. [Detailed Implementation Steps](#4-detailed-implementation-steps)
5. [URL Routing Plan](#5-url-routing-plan)
6. [Settings Changes](#6-settings-changes)
7. [File-by-File Mapping (Template → Backend)](#7-file-by-file-mapping-template--backend)

---

## 1. Frontend Templates Summary

| Template | Purpose | Key Data Entities | Forms/Actions |
|---|---|---|---|
| `index.html` | Marketplace homepage | Categories, Products, Vendors, Deals, Sponsored Ads, Cart items, Favorites | Search (`/search?q=`), Filter (category, price, rating), Contact form, Add to cart, Add to favorites |
| `login.html` | Buyer login | Buyer user (email, password) | Login form → redirects to `index.html` |
| `seller-register-login.html` | Seller login + registration | Seller user (name, email, password, address, phone, store name, store category, rating) | Login form → redirects to `seller-dashboard.html`, Registration form |
| `product.html` | Product detail page | Product (name, price, description, rating, rating count, category, vendor, features, sponsored flag), Compare products | Add to cart, Add to favorites, Compare products |
| `seller-dashboard.html` | Seller dashboard panel | Products, Offers/Deals, Orders, Sponsored Ads, Stats/KPIs | Add product (with image upload), Create offer, Create sponsored ad (2 types) |
| `store.html` | Individual vendor storefront | Vendor (name, category, rating), Vendor's products | — |
| `vendors.html` | All vendors listing | Vendors (name, category, rating, avatar) | Link to individual store |

---

## 2. Models to Add in `base/models.py`

### 2.1 `Category`
Extracted from: `index.html` (categories section, filter datalist), `seller-dashboard.html` (product form datalist), `seller-register-login.html` (store category datalist)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `name` | `CharField(max_length=100, unique=True)` | e.g. إلكترونيات, أزياء وملابس |
| `description` | `TextField(blank=True)` | Optional subcategory text like "هواتف • سماعات • شواحن" |
| `slug` | `SlugField(unique=True, allow_unicode=True)` | For URL-friendly category routes |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

---

### 2.2 `Vendor` (Seller / Store)
Extracted from: `vendors.html`, `store.html`, `index.html` (vendors section), `seller-dashboard.html` (sidebar store info), `seller-register-login.html` (registration form)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `user` | `OneToOneField(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='vendor_profile')` | Links to Django user |
| `store_name` | `CharField(max_length=150)` | e.g. TechZone, StyleHub |
| `category` | `ForeignKey(Category, on_delete=SET_NULL, null=True)` | Primary store category |
| `rating` | `DecimalField(max_digits=2, decimal_places=1, default=0)` | e.g. 4.8 |
| `address` | `CharField(max_length=300, blank=True)` | From registration form |
| `phone` | `CharField(max_length=20, blank=True)` | Optional, from registration form |
| `avatar` | `ImageField(upload_to='vendors/avatars/', blank=True)` | Vendor avatar |
| `is_active` | `BooleanField(default=True)` | Status: active/inactive |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

---

### 2.3 `Product`
Extracted from: `index.html` (products grid, deals, sponsored), `product.html` (detail page), `seller-dashboard.html` (add product form, products table), `store.html` (vendor products)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `vendor` | `ForeignKey(Vendor, on_delete=CASCADE, related_name='products')` | Which seller owns this |
| `name` | `CharField(max_length=200)` | Product name |
| `description` | `TextField(blank=True)` | Product description |
| `price` | `DecimalField(max_digits=10, decimal_places=2)` | Current price |
| `stock` | `PositiveIntegerField(default=0)` | Inventory count |
| `category` | `ForeignKey(Category, on_delete=SET_NULL, null=True)` | Product category |
| `rating` | `DecimalField(max_digits=2, decimal_places=1, default=0)` | Average rating |
| `rating_count` | `PositiveIntegerField(default=0)` | Number of ratings (e.g. 1,248 تقييم) |
| `image` | `ImageField(upload_to='products/images/')` | Product image (from file upload form) |
| `is_active` | `BooleanField(default=True)` | Active or out-of-stock |
| `is_sponsored_badge` | `BooleanField(default=False)` | Shows "ممول" badge on product image in grid |
| `slug` | `SlugField(unique=True, allow_unicode=True)` | URL-friendly identifier |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |
| `updated_at` | `DateTimeField(auto_now=True)` | — |

---

### 2.4 `Deal` (Offer/Discount)
Extracted from: `index.html` (deals section), `seller-dashboard.html` (offers form)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name='deals')` | Which product |
| `discount_percentage` | `PositiveIntegerField()` | e.g. 25, 15, 40 |
| `original_price` | `DecimalField(max_digits=10, decimal_places=2)` | Price before discount |
| `start_date` | `DateField()` | Offer start |
| `end_date` | `DateField()` | Offer end |
| `is_active` | `BooleanField(default=True)` | — |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

---

### 2.5 `SponsoredAd`
Extracted from: `index.html` (sponsored ads section), `seller-dashboard.html` (ads form — 2 types)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name='sponsored_ads')` | The advertised product |
| `vendor` | `ForeignKey(Vendor, on_delete=CASCADE, related_name='sponsored_ads')` | The paying vendor |
| `ad_type` | `CharField(max_length=20, choices=[('section', 'Sponsored Section'), ('badge', 'Badge on Image')])` | Two types from seller dashboard |
| `budget` | `DecimalField(max_digits=10, decimal_places=2)` | Ad budget, e.g. $120 |
| `duration_days` | `PositiveIntegerField()` | e.g. 7 days |
| `status` | `CharField(max_length=20, choices=[('active', 'Active'), ('pending', 'Pending Review'), ('expired', 'Expired'), ('rejected', 'Rejected')])` | From ads table in dashboard |
| `start_date` | `DateField(auto_now_add=True)` | — |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

---

### 2.6 `Cart` and `CartItem`
Extracted from: `index.html` (cart drawer overlay), `product.html` (add to cart)

**Cart**:

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `user` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, null=True, blank=True)` | Logged-in user (nullable for guests) |
| `session_key` | `CharField(max_length=40, null=True, blank=True)` | For guest cart |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

**CartItem**:

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `cart` | `ForeignKey(Cart, on_delete=CASCADE, related_name='items')` | Parent cart |
| `product` | `ForeignKey(Product, on_delete=CASCADE)` | The product |
| `quantity` | `PositiveIntegerField(default=1)` | From cart drawer: "الكمية: 1", "الكمية: 2" |
| `added_at` | `DateTimeField(auto_now_add=True)` | — |

---

### 2.7 `Favorite`
Extracted from: `index.html` (favorites drawer overlay), `product.html` (add to favorites button)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `user` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name='favorites')` | — |
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name='favorited_by')` | — |
| `added_at` | `DateTimeField(auto_now_add=True)` | — |

**Constraint**: `unique_together = ('user', 'product')` to prevent duplicates.

---

### 2.8 `Order` and `OrderItem`
Extracted from: `seller-dashboard.html` (orders table with: order number, customer, total, status, date)

**Order**:

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `order_number` | `CharField(max_length=20, unique=True)` | e.g. #10231 |
| `buyer` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True)` | Customer |
| `vendor` | `ForeignKey(Vendor, on_delete=SET_NULL, null=True)` | Which vendor's order |
| `total` | `DecimalField(max_digits=10, decimal_places=2)` | Order total |
| `shipping_cost` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | From cart summary: "الشحن (تقديري)" |
| `status` | `CharField(max_length=20, choices=[('preparing', 'قيد التجهيز'), ('shipped', 'تم الشحن'), ('delivered', 'تم التسليم'), ('cancelled', 'ملغي')])` | From orders table |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

**OrderItem**:

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `order` | `ForeignKey(Order, on_delete=CASCADE, related_name='items')` | Parent order |
| `product` | `ForeignKey(Product, on_delete=SET_NULL, null=True)` | — |
| `quantity` | `PositiveIntegerField(default=1)` | — |
| `price_at_order` | `DecimalField(max_digits=10, decimal_places=2)` | Price snapshot at time of order |

---

### 2.9 `ContactMessage`
Extracted from: `index.html` (contact form: name, email, message)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `name` | `CharField(max_length=150)` | Sender name |
| `email` | `EmailField()` | Sender email |
| `message` | `TextField()` | Message body |
| `is_read` | `BooleanField(default=False)` | Admin tracking |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

---

### 2.10 `VendorStats` (Optional — for seller dashboard analytics)
Extracted from: `seller-dashboard.html` (stats section: visit growth, avg rating, conversion rate, weekly summary)

| Field | Type | Notes |
|---|---|---|
| `id` | `BigAutoField` (auto) | Primary key |
| `vendor` | `ForeignKey(Vendor, on_delete=CASCADE, related_name='stats')` | — |
| `week_start` | `DateField()` | Week period |
| `views` | `PositiveIntegerField(default=0)` | Weekly views (e.g. 1,240) |
| `sales_total` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | Monthly sales (e.g. $3,980) |
| `conversion_rate` | `DecimalField(max_digits=4, decimal_places=2, default=0)` | e.g. 2.9% |
| `visit_growth` | `DecimalField(max_digits=5, decimal_places=2, default=0)` | e.g. +18% |
| `best_product` | `ForeignKey(Product, on_delete=SET_NULL, null=True, blank=True)` | Best selling product |
| `created_at` | `DateTimeField(auto_now_add=True)` | — |

---

## 3. Backend Functionalities (Ranked by Priority)

> **Ranking criteria**: How heavily the feature is referenced in the frontend templates, whether forms/links exist for it, and whether other features depend on it.

### 🔴 Priority 1 — Critical (Referenced Everywhere, Core Business Logic)

| # | Functionality | Referenced In | Why Critical |
|---|---|---|---|
| 1 | **User Authentication (Buyer + Seller)** | `login.html`, `seller-register-login.html`, `seller-dashboard.html`, `index.html` (topbar "الحساب" link) | Every page links to login; seller dashboard requires auth guard; buyer vs. seller role separation |
| 2 | **Product CRUD** | `seller-dashboard.html` (add form + products table), `index.html` (grid), `product.html` (detail), `store.html` (vendor products) | Products are the core entity — every page displays them |
| 3 | **Cart System** | `index.html` (cart drawer + "إضافة للسلة" buttons on every product), `product.html` ("شراء الآن", "إضافة للسلة"), footer links to checkout | Cart is present in every product interaction; checkout flow depends on it |
| 4 | **Category System** | `index.html` (categories grid + filter datalist), `seller-dashboard.html` (category datalist on product form), `seller-register-login.html` (store category) | Categories are used in filters, product creation, and vendor registration |
| 5 | **Vendor/Store System** | `vendors.html`, `store.html`, `index.html` (vendors section), `seller-dashboard.html`, `seller-register-login.html` | Vendors are displayed on every page; multi-tenant architecture depends on this |

### 🟡 Priority 2 — Important (Has Dedicated Frontend Sections/Forms)

| # | Functionality | Referenced In | Why Important |
|---|---|---|---|
| 6 | **Favorites/Wishlist** | `index.html` (favorites drawer + "مفضلة" buttons), `product.html` ("مفضلة" button) | Dedicated overlay drawer, buttons on every product card |
| 7 | **Deals/Offers System** | `index.html` (deals section with discount badges), `seller-dashboard.html` (offer creation form) | Dedicated section on homepage; seller can create offers with date ranges |
| 8 | **Sponsored Ads System** | `index.html` (sponsored section + "ممول" badge on products), `seller-dashboard.html` (2 ad creation forms + ads table) | Dedicated homepage section; two types of ads; ad management table |
| 9 | **Order Management** | `seller-dashboard.html` (orders table with status), `index.html` (cart checkout flow) | Orders are the result of the checkout process; seller needs to manage them |
| 10 | **Search & Filtering** | `index.html` (hero search form → `/search`, filter sidebar with category/price/rating) | Search form is prominently placed in hero; filter sidebar is a major UI element |

### 🟢 Priority 3 — Nice to Have (Supporting Features)

| # | Functionality | Referenced In | Why Nice to Have |
|---|---|---|---|
| 11 | **Contact Form Processing** | `index.html` (contact section form) | Single form, straightforward implementation |
| 12 | **Product Comparison** | `product.html` (compare modal with table) | Modal exists but noted as "Backend fills data" |
| 13 | **Seller Dashboard Analytics/Stats** | `seller-dashboard.html` (KPIs: views, sales, conversion, growth) | Stats are nice; placeholder data exists; can be computed from orders |
| 14 | **Image Upload & Media Handling** | `seller-dashboard.html` (product image file input) | Required for product creation but is a support feature |
| 15 | **Seller Dashboard Access Control** | `seller-dashboard.html` (note: "يجب أن يعرضه الـ Backend للبائع فقط") | Middleware/decorator to protect seller-only pages |

### ⚪ Priority 4 — Deferred (Can Be Added Later)

| # | Functionality | Notes |
|---|---|---|
| 16 | **Rate Limiting** | Not referenced in any template; add for API security later |
| 17 | **Caching** | Not referenced in templates; add for performance optimization later |
| 18 | **Checkout/Payment Processing** | `cart-checkout.html` is referenced but does NOT exist yet as a template |
| 19 | **Product Reviews/Ratings System** | Ratings are displayed but no review writing form exists in templates |

---

## 4. Detailed Implementation Steps

### Step 1: Project Configuration & Settings
**File**: `vendor/settings.py`

1. Add `TEMPLATES.DIRS` to include the `templates` folder:
   ```python
   "DIRS": [BASE_DIR / "templates"],
   ```
2. Add `STATICFILES_DIRS` to serve static assets:
   ```python
   STATICFILES_DIRS = [BASE_DIR / "static"]
   ```
3. Configure `MEDIA_URL` and `MEDIA_ROOT` for file uploads (product images, vendor avatars):
   ```python
   MEDIA_URL = "/media/"
   MEDIA_ROOT = BASE_DIR / "media"
   ```
4. Add `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` settings:
   ```python
   LOGIN_URL = "/login/"
   LOGIN_REDIRECT_URL = "/"
   LOGOUT_REDIRECT_URL = "/"
   ```

---

### Step 2: Create All Models in `base/models.py`
**File**: `base/models.py`

Write all 10+ models as described in [Section 2](#2-models-to-add-in-basemodelspy) above, in this order (respecting FK dependencies):

1. `Category`
2. `Vendor`
3. `Product`
4. `Deal`
5. `SponsoredAd`
6. `Cart`
7. `CartItem`
8. `Favorite`
9. `Order`
10. `OrderItem`
11. `ContactMessage`
12. `VendorStats` (optional)

Then run:
```bash
python manage.py makemigrations base
python manage.py migrate
```

---

### Step 3: Register Models in Admin
**File**: `base/admin.py`

Register all models with `admin.site.register(...)` with appropriate `list_display`, `list_filter`, `search_fields` for easy admin management. Key models to customize:

- `ProductAdmin` — list_display: name, vendor, price, stock, is_active, is_sponsored_badge
- `OrderAdmin` — list_display: order_number, buyer, vendor, total, status, created_at
- `SponsoredAdAdmin` — list_display: product, vendor, ad_type, budget, status
- `DealAdmin` — list_display: product, discount_percentage, start_date, end_date, is_active

---

### Step 4: Implement Authentication System (Priority 1)
**Files**: `base/views.py`, `base/urls.py`, `base/forms.py` (new file)

#### 4.1 Create `base/forms.py` with:
- `BuyerLoginForm` — fields: email, password
- `SellerLoginForm` — fields: email, password
- `SellerRegistrationForm` — fields: full_name, email, password, address, store_name, store_category (datalist), rating, phone

#### 4.2 Create views in `base/views.py`:
- `buyer_login_view(request)` — handles `login.html` form POST, authenticates, redirects to `/`
- `seller_login_view(request)` — handles `seller-register-login.html` login form POST, authenticates, redirects to `/seller/dashboard/`
- `seller_register_view(request)` — handles `seller-register-login.html` registration form POST, creates User + Vendor, auto-logs in, redirects to `/seller/dashboard/`
- `logout_view(request)` — logs out, redirects to `/`

#### 4.3 User Role Differentiation:
- Option A (recommended): Add an `is_seller` BooleanField to a custom User model or a `UserProfile` model
- Option B: Use Django Groups — create a "Seller" group and check membership
- The `user` field on `Vendor` model already establishes the relationship; check if `hasattr(request.user, 'vendor_profile')` to determine if the user is a seller

#### 4.4 Create a `@seller_required` decorator:
Protects `seller-dashboard.html` and seller-only routes. If user is not a seller, redirect to seller login page.

---

### Step 5: Implement Product System (Priority 1)
**Files**: `base/views.py`, `base/urls.py`, `base/forms.py`

#### 5.1 Views:
- `home_view(request)` — renders `index.html` with context:
  - `categories` — all categories
  - `deals` — active deals with products
  - `sponsored_ads` — active sponsored ads (type: section)
  - `products` — latest products (with `is_sponsored_badge` for badge display)
  - `vendors` — top vendors
  - `cart_count` — number of items in user's cart
  - `favorites_count` — number of items in user's favorites
  - `cart_items` — items for cart drawer
  - `favorite_items` — items for favorites drawer

- `product_detail_view(request, slug)` — renders `product.html` with:
  - `product` — the product object
  - `compare_product` — optional comparison product (from query param or session)

- `store_view(request, vendor_id)` — renders `store.html` with:
  - `vendor` — vendor info
  - `products` — vendor's products

- `vendors_list_view(request)` — renders `vendors.html` with:
  - `vendors` — all active vendors

#### 5.2 Seller Dashboard Views (protected by `@seller_required`):
- `seller_dashboard_view(request)` — renders `seller-dashboard.html` with:
  - `vendor` — current seller's vendor profile
  - `products` — seller's products
  - `orders` — orders for this seller
  - `sponsored_ads` — seller's ads
  - `stats` — seller's statistics
  - KPI aggregates: product count, weekly views, monthly sales

- `seller_add_product_view(request)` — handles POST from add product form
- `seller_add_offer_view(request)` — handles POST from offer form
- `seller_create_ad_view(request)` — handles POST from sponsored ad forms (both types)

---

### Step 6: Implement Cart System (Priority 1)
**Files**: `base/views.py`, `base/urls.py`

#### 6.1 Cart Logic:
- Use session-based cart for guest users and database cart for logged-in users
- Cart helper function: `get_or_create_cart(request)` — checks for user or session key

#### 6.2 Views:
- `add_to_cart_view(request, product_id)` — adds item to cart, redirects back (the "إضافة للسلة" links)
- `remove_from_cart_view(request, item_id)` — removes item from cart
- `update_cart_item_view(request, item_id)` — updates quantity
- `cart_summary_view(request)` — returns cart data for the drawer (subtotal, shipping estimate, total)

#### 6.3 Context Processor (recommended):
Create `base/context_processors.py` with a `cart_context(request)` function that injects `cart_items` and `cart_count` into every template so the topbar always shows the correct count.

---

### Step 7: Implement Favorites System (Priority 2)
**Files**: `base/views.py`, `base/urls.py`

#### 7.1 Views:
- `add_to_favorites_view(request, product_id)` — toggles favorite (requires login)
- `remove_from_favorites_view(request, product_id)` — removes from favorites

#### 7.2 Context Processor:
Add `favorites_context(request)` to inject `favorite_items` and `favorites_count` into every template.

---

### Step 8: Implement Deals & Sponsored Ads (Priority 2)
**Files**: `base/views.py`

#### 8.1 Deals:
- Already handled in `home_view` context: query `Deal.objects.filter(is_active=True, end_date__gte=today)` with `select_related('product')`
- Computed property on `Deal`: `discounted_price = original_price * (1 - discount_percentage / 100)`

#### 8.2 Sponsored Ads:
- In `home_view`: query `SponsoredAd.objects.filter(status='active', ad_type='section')` for the sponsored section
- In product listing: annotate products with `is_sponsored_badge=True` for badge display
- Seller creates ads via dashboard POST forms

---

### Step 9: Implement Order System (Priority 2)
**Files**: `base/views.py`, `base/urls.py`

#### 9.1 Views:
- `checkout_view(request)` — creates Order + OrderItems from cart, clears cart
- `seller_update_order_status_view(request, order_id)` — seller updates order status (referenced in dashboard note: `/seller/orders/10231/update`)

#### 9.2 Order Number Generation:
Auto-generate sequential order numbers like `#10231`.

---

### Step 10: Implement Search & Filter (Priority 2)
**Files**: `base/views.py`, `base/urls.py`

#### 10.1 Search View:
- `search_view(request)` — handles the hero search form (`/search?q=...`)
- Query params: `q` (text search), `category` (filter), `minPrice`, `maxPrice`, `rating`
- Returns filtered products using `Q` objects and `filter()` chains
- Renders `index.html` (or a dedicated search results template if created later)

---

### Step 11: Implement Contact Form (Priority 3)
**Files**: `base/views.py`, `base/urls.py`

- `contact_view(request)` — handles contact form POST, creates `ContactMessage`, shows success feedback
- Optional: send email notification to admin

---

### Step 12: Implement Product Comparison (Priority 3)
**Files**: `base/views.py`

- Store comparison products in session
- `add_to_compare_view(request, product_id)` — adds product to comparison list (stored in session)
- `product_detail_view` already passes `compare_product` — fill this from session data

---

## 5. URL Routing Plan

### `base/urls.py`

```
# Public pages
/                                   → home_view               (index.html)
/login/                             → buyer_login_view         (login.html)
/seller/auth/                       → seller_auth_view         (seller-register-login.html)
/logout/                            → logout_view

# Product pages
/product/<slug:slug>/               → product_detail_view      (product.html)
/store/<int:vendor_id>/             → store_view               (store.html)
/vendors/                           → vendors_list_view        (vendors.html)
/search/                            → search_view              (search results)

# Cart (POST endpoints)
/cart/add/<int:product_id>/         → add_to_cart_view
/cart/remove/<int:item_id>/         → remove_from_cart_view
/cart/update/<int:item_id>/         → update_cart_item_view
/checkout/                          → checkout_view

# Favorites (POST endpoints)
/favorites/add/<int:product_id>/    → add_to_favorites_view
/favorites/remove/<int:product_id>/ → remove_from_favorites_view

# Contact
/contact/                           → contact_view

# Comparison
/compare/add/<int:product_id>/      → add_to_compare_view

# Seller Dashboard (protected — @seller_required)
/seller/dashboard/                  → seller_dashboard_view    (seller-dashboard.html)
/seller/products/add/               → seller_add_product_view
/seller/offers/add/                 → seller_add_offer_view
/seller/ads/create/                 → seller_create_ad_view
/seller/orders/<int:order_id>/update/ → seller_update_order_status_view
```

### `vendor/urls.py`
```python
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("base.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 6. Settings Changes

### `vendor/settings.py` changes needed:

| Setting | Current | Change To |
|---|---|---|
| `TEMPLATES.DIRS` | `[]` | `[BASE_DIR / "templates"]` |
| `STATICFILES_DIRS` | (missing) | `[BASE_DIR / "static"]` |
| `MEDIA_URL` | (missing) | `"/media/"` |
| `MEDIA_ROOT` | (missing) | `BASE_DIR / "media"` |
| `LOGIN_URL` | (missing) | `"/login/"` |
| `LOGIN_REDIRECT_URL` | (missing) | `"/"` |
| `LOGOUT_REDIRECT_URL` | (missing) | `"/"` |
| `context_processors` | (default) | Add `"base.context_processors.cart_context"` and `"base.context_processors.favorites_context"` |

---

## 7. File-by-File Mapping (Template → Backend)

| Template | View Function | URL Pattern | Context Data Needed |
|---|---|---|---|
| `index.html` | `home_view` | `/` | categories, deals, sponsored_ads, products, vendors, cart_items, favorite_items, cart_count, favorites_count |
| `login.html` | `buyer_login_view` | `/login/` | form (email, password), errors |
| `seller-register-login.html` | `seller_auth_view` | `/seller/auth/` | login_form, register_form, categories (for datalist), errors |
| `product.html` | `product_detail_view` | `/product/<slug>/` | product, compare_product, vendor |
| `seller-dashboard.html` | `seller_dashboard_view` | `/seller/dashboard/` | vendor, products, orders, sponsored_ads, stats, kpis |
| `store.html` | `store_view` | `/store/<vendor_id>/` | vendor, products |
| `vendors.html` | `vendors_list_view` | `/vendors/` | vendors |

---

## New Files to Create

| File | Purpose |
|---|---|
| `base/models.py` | All 12 models (overwrite existing empty file) |
| `base/views.py` | All view functions (overwrite existing empty file) |
| `base/urls.py` | All URL patterns (overwrite existing empty file) |
| `base/forms.py` | Django forms for login, registration, product add, offer, ad, contact |
| `base/admin.py` | Admin registrations for all models (overwrite existing empty file) |
| `base/context_processors.py` | Cart and favorites context processors |
| `base/decorators.py` | `@seller_required` decorator |
| `base/templatetags/` (optional) | Custom template tags if needed for computed values |

---

## Implementation Order (Summary)

```
Step 1  → Settings configuration
Step 2  → Models (all 12)
Step 3  → Admin registration
Step 4  → Authentication (login, register, logout, seller guard)
Step 5  → Product system (CRUD, detail, listing)
Step 6  → Cart system (add, remove, update, context processor)
Step 7  → Favorites system (add, remove, context processor)
Step 8  → Deals & Sponsored Ads
Step 9  → Order system (checkout, status updates)
Step 10 → Search & Filtering
Step 11 → Contact form
Step 12 → Product comparison
```

Each step can be implemented and tested independently. Steps 1–3 are foundational and must come first. Steps 4–6 are the core user experience. Steps 7–12 extend the platform.

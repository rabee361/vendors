# Checkout Page, Account Modal & Button Fixes — Implementation Plan

This plan covers four connected features: model schema changes, an account settings modal, a full checkout page, and instant button state toggling on the home page. All CSS goes into [main.css](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/static/css/main.css), all views are class-based, and all new views get a test.

---

## Proposed Changes

### Component 1 — Model Changes

Schema additions to [CustomUser](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#11-42) and cleanup of [Buyer](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#43-51).

#### [MODIFY] [models.py](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py)

- **Add to [CustomUser](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#11-42):**
  - `avatar = models.ImageField(upload_to='users/avatars/', blank=True, null=True)`
  - `phone = models.CharField(max_length=20, blank=True, null=True)`
  - Update [clean()](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/forms.py#92-100) to reference `self.avatar` instead of `self.image`
- **Modify [Buyer](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#43-51):**
  - Remove the [phone](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/tests/tests.py#51-64) field (it now lives on [CustomUser](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#11-42))

> [!IMPORTANT]
> This requires a migration. Any existing `Buyer.phone` data will be lost unless migrated manually. If there is real data in `Buyer.phone`, a data migration should be added to copy values before dropping the column.

#### Migration
```
python manage.py makemigrations base
python manage.py migrate
```

---

### Component 2 — Account Modal

A slide-in overlay modal (same pattern as cart/favorites drawers) for viewing/editing account info.

#### [NEW] [account.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/components/account.html)

New component included in [base.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/base.html), structured as:
- **Avatar section**: Shows `user.avatar` image or a fallback circle with the first letter of `user.first_name` (use existing `.avatar` CSS class)
- **Avatar upload**: File input to change the avatar image
- **Display name**: Editable text input pre-filled with `user.first_name`
- **Email**: Read-only display of `user.email`
- **Phone**: Editable input pre-filled with `user.phone` (if set)
- **Change password**: A link/button that navigates to the existing change-password page (`{% url 'change_password' %}`)
- **Save button**: Submits the form via standard POST (not HTMX, since there's a file upload)
- Open/close uses the same overlay + drawer pattern as cart/favorites ([toggleOverlay('account')](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/static/js/overlay.js#1-10) / [closeOverlay('account')](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/static/js/overlay.js#11-15))

#### [MODIFY] [base.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/base.html)

- Add `{% include 'components/account.html' %}` alongside the cart/favorites includes (only when `user.is_authenticated`)

#### [MODIFY] [topbar.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/components/topbar.html)

- Change the account icon link (line 32) from `href=""` to `onclick="toggleOverlay('account')"` (same pattern as cart/favorites)
- Change the unauthenticated link (line 34) from `href="login.html"` to `href="{% url 'login' %}"`

#### [NEW] `AccountUpdateForm` in [forms.py](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/forms.py)

Fields: `display_name` (CharField), [phone](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/tests/tests.py#51-64) (CharField, optional), `avatar` (ImageField, optional)

#### [MODIFY] [base.py (views)](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/views/base.py)

Add `AccountUpdateView(View)`:
- **POST**: Validates form, updates `user.first_name`, `user.phone`, `user.avatar` (if provided), saves, redirects back with a success message
- Requires `@login_required` (or check `request.user.is_authenticated`)

#### [MODIFY] [urls.py](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/urls.py)

- Add: `path('account/update/', base.AccountUpdateView.as_view(), name='account_update')`
- Add: `path('auth/change-password/', base.ChangePasswordView.as_view(), name='change_password')` (if not already registered)

#### [MODIFY] [main.css](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/static/css/main.css)

Add CSS for the account modal:
- `.account-avatar` — large circular avatar (80×80px) using the existing gradient fallback
- `.account-avatar-letter` — centered first-letter display inside the avatar circle
- `.account-form` — form layout (grid, gaps) consistent with existing form styling
- `.account-info` — read-only email display style

---

### Component 3 — Checkout Page

A full-page checkout form with order summary and shipping fields.

#### [MODIFY] [checkout.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/checkout.html)

Extends [base.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/base.html). Two-column layout (on desktop):

**Left column — Shipping form:**
- Full name (pre-filled from `user.first_name` if authenticated)
- Phone number (pre-filled from `user.phone` if authenticated)
- City (text input)
- Full address (textarea)
- Notes (textarea, optional)

**Right column — Order summary:**
- Cart items grouped by vendor (reuse the `vendor-cart-group` pattern from [cart.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/components/cart.html))
- Per-vendor subtotal
- Global subtotal, shipping cost (placeholder $0), grand total
- "تأكيد الطلب" (Place Order) submit button

#### [NEW] `CheckoutForm` in [forms.py](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/forms.py)

Fields: `full_name`, [phone](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/tests/tests.py#51-64), `city`, `address`, `notes` (optional)

#### [MODIFY] [base.py (views)](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/views/base.py)

Add `CheckoutView(View)`:
- **GET**: Loads cart via [CartService](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/cart.py#4-125), if cart is empty redirect to home. Renders [checkout.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/checkout.html) with `grouped_items`, `cart_total`, and the `CheckoutForm`
- **POST**: Validates form. Creates one [Order](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#185-201) per vendor (using existing [Order](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#185-201) + [OrderItem](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#202-211) models). Clears the cart. Redirects to home with a success message.
- Requires authentication (redirect to login if anonymous)

#### [MODIFY] [urls.py](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/urls.py)

- Add: `path('checkout/', base.CheckoutView.as_view(), name='checkout')`

#### [MODIFY] [cart.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/components/cart.html)

- Update the "إتمام الشراء من..." button `href` from `#` to `{% url 'checkout' %}`

#### [MODIFY] [main.css](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/static/css/main.css)

Add checkout-specific CSS:
- `.checkout-grid` — two-column layout (shipping form + order summary)
- `.checkout-section` — card-styled section for form/summary
- `.order-summary` — summary items list style
- `.checkout-total` — grand total row styling
- Responsive: stack to single column on mobile

---

### Component 4 — Instant Button State Toggle (index.html)

Fix so favorite and add-to-cart buttons change color **instantly** without a page reload.

#### [MODIFY] [cart.py (CartService)](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/cart.py)

Add `cart_product_ids` to the dict returned by [get_context()](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/favorite.py#59-78):
```python
'cart_product_ids': [str(pid) for pid in product_ids_in_cart]
```
This lets templates know which products are already in the cart for initial `.active` state.

#### [MODIFY] [index.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/index.html)

**Favorite buttons** (lines 304–306 in the products loop, and similar hard-coded ones):
- Add `hx-on::after-request="this.classList.toggle('active')"` attribute to every `.paction-btn.fav` button

**Cart buttons** (lines 301–303 in the products loop, and similar hard-coded ones):
- Add `hx-on::after-request="this.classList.toggle('active')"` attribute to every `.paction-btn.cart` button
- Add initial `active` class: `{% if product.id|slugify in cart_product_ids %}active{% endif %}`

#### [MODIFY] [product.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/product.html)

Same changes as above for the fav and cart buttons on the product detail page (lines 106–111).

#### [MODIFY] [products.html](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/templates/base/products.html)

Same changes for the product list page buttons (if they have fav/cart buttons).

---

## Verification Plan

### Automated Tests

All tests run with:
```
python manage.py test base.tests -v2
```

#### [NEW] Test in [tests.py](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/tests/tests.py)

**`CheckoutViewTests`:**
1. `test_checkout_get_empty_cart` — GET `/checkout/` with empty cart → redirects to home
2. `test_checkout_get_with_items` — Add items to cart, GET → returns 200, shows items
3. `test_checkout_post_creates_orders` — POST with valid shipping data → creates [Order](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#185-201) + [OrderItem](file:///c:/Users/eng.Rabee/Django%20Projects/vendor/base/models.py#202-211) records, clears cart, redirects
4. `test_checkout_requires_auth` — Anonymous user GET → redirects to login

**`AccountUpdateViewTests`:**
1. `test_account_update_display_name` — POST new display_name → `user.first_name` updates
2. `test_account_update_phone` — POST phone number → `user.phone` updates
3. `test_account_update_requires_auth` — Anonymous POST → redirects to login

**`ButtonStateTests`:**
1. `test_cart_context_has_product_ids` — After adding to cart, `cart_product_ids` is present in context and contains the correct product ID

### Manual Verification
- Open the home page, click the heart (fav) button on a product → should instantly turn red, toast appears
- Click again → turns back to default, toast says "removed"
- Click the cart button → should instantly turn green, toast appears
- Click the user icon in topbar → account modal opens with avatar/name/email/phone
- Update display name and phone, save → modal closes, data persists on re-open
- Add items to cart → click "إتمام الشراء" → checkout page with summary + form
- Fill shipping form and submit → order placed, cart emptied, redirected home

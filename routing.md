# توثيق مسارات المستخدم (Routing Documentation)

يوضح هذا الملف المسارات (URLs) وسير العمل (Workflows) لمختلف أنواع المستخدمين في المنصة.

---

## 1. مسار المشتري (Customer / Buyer)
يمثل هذا المسار رحلة المستخدم العادي من التصفح إلى الشراء.

*   **البداية (الصفحة الرئيسية):** `localhost:8000/`
    *   تصفح المنتجات المميزة، العروض، وأقسام المتجر.
*   **التسجيل / الدخول:**
    *   إنشاء حساب جديد: `localhost:8000/signup/`
    *   تسجيل الدخول: `localhost:8000/login/` (اختيار حساب مشتري)
*   **تصفح المنتجات:**
    *   قائمة كافة المنتجات: `localhost:8000/products/`
    *   عرض تفاصيل منتج معين: `localhost:8000/products/<id>/`
    *   تصفح الأصناف: `localhost:8000/categories/`
*   **إدارة السلة والمفضلة:**
    *   عرض السلة: `localhost:8000/cart/`
    *   تفعيل/إلغاء المفضلة: `localhost:8000/favorites/toggle/<id>/`
*   **إتمام الشراء:**
    *   صفحة الدفع لمتجر محدد: `localhost:8000/checkout/<vendor_id>/`
    *   *بعد النجاح يتم التوجيه إلى الصفحة الرئيسية مع رسالة تأكيد.*

---

## 2. مسار البائع (Seller / Vendor)
يمثل هذا المسار رحلة التاجر في إدارة متجره ومنتجاته.

*   **التسجيل والتحقق:**
    *   إنشاء حساب تاجر: `localhost:8000/vendor/signup/`
    *   التحقق من الرمز (OTP): `localhost:8000/verify-otp/`
*   **لوحة التحكم (Dashboard):**
    *   الرئيسية للبائع: `localhost:8000/vendor/dashboard/` (تحتوي على إحصائيات سريعة).
*   **إدارة المنتجات:**
    *   قائمة المنتجات: `localhost:8000/vendor/products/`
    *   إضافة منتج جديد: `localhost:8000/vendor/products/add/`
    *   تحديث/حذف: `localhost:8000/vendor/products/update/<id>/` | `delete/<id>/`
*   **إدارة العروض والإعلانات:**
    *   إحصائيات العروض: `localhost:8000/vendor/offers/`
    *   إدارة الإعلانات الممولة: `localhost:8000/vendor/ads/`
*   **إدارة الطلبات:**
    *   عرض الطلبات الواردة: `localhost:8000/vendor/orders/`
    *   تحديث حالة الطلب: `localhost:8000/vendor/orders/update/<id>/`

---

## 3. مسار المشرف / المدير (Admin / Moderator)
يمثل هذا المسار الصلاحيات الإدارية والرقابية على المنصة.

*   **تسجيل الدخول:**
    *   صفحة دخول المشرفين: `localhost:8000/moderator/login/`
*   **الإحصائيات العامة:**
    *   لوحة تحكم المشرف: `localhost:8000/moderator/`
*   **إدارة المنصة:**
    *   الرقابة على المتاجر (Vendors): `localhost:8000/moderator/vendors/`
    *   إدارة أصناف المتاجر: `localhost:8000/moderator/categories/`
    *   إضافة أصناف جديدة: `localhost:8000/moderator/categories/add/`
*   **إدارة الحسابات:**
    *   قائمة مشرفي النظام: `localhost:8000/moderator/list/`

---

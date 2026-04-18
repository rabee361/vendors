# 🚀 دليل إعداد وتشغيل المشروع

هذا الملف يشرح كيفية تشغيل المشروع على بيئة التطوير المحلية (Local Environment) وبيئة الإنتاج (Production / Global Environment). 
المشروع يعتمد على قاعدة بيانات **SQLite** 💾 لكلا البيئتين.

---

## 💻 1. بيئة التطوير المحلية (Local Environment)

### 🛠️ المتطلبات المسبقة:
- تثبيت Python (يفضل 3.12) 🐍.
- أداة `pip` لإدارة الحزم 📦.

### 📝 خطوات التشغيل:

1. **إنشاء البيئة الافتراضية (Virtual Environment):**
   من الجذر الرئيسي للمشروع، قم بتشغيل الأمر التالي:
   ```cmd
   python -m venv .venv
   ```

2. **تفعيل البيئة الافتراضية:**
   نظراً لأنك تستخدم نظام Windows 🪟، استخدم الأمر التالي:
   ```cmd
   .venv\Scripts\activate
   ```

3. **تثبيت الحزم والمتطلبات الأساسية:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **تطبيق تجهيزات قاعدة البيانات (Migrations):**
   سيقوم هذا الأمر بتهيئة قاعدة البيانات `db.sqlite3` 🗄️:
   ```cmd
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **تعبئة داتا مزيفة:**
   ```cmd
   python manage.py populate
   ```

6. **تشغيل خادم التطوير:**
   ```cmd
   python manage.py runserver
   ```
   الآن، المشروع يعمل محلياً! يمكنك زيارته عبر المتصفح 🌐: `http://localhost:8000`

---

## 🌍 2. بيئة الإنتاج (Production / Global Environment)

بالنسبة لبيئة الإنتاج، يتم تشغيل المشروع عبر **Docker** 🐳 لضمان الاستقرار وسهولة النشر المطلق.

### 🛠️ المتطلبات المسبقة:
- تثبيت وتفعيل **Docker** 🐋 على الخادم أو جهازك.

### 📝 خطوات التشغيل:

1. **بناء صورة المشروع (Docker Image):**
   يتكفل الـ `dockerfile` بتجهيز كل شيء (تثبيت الحزم، إعداد المستخدم، الخ):
   ```cmd
   docker build -t vendor-app .
   ```

2. **إنشاء مجلدات دائمة للملفات الثابتة والوسائط على الخادم:**
   هذه المجلدات يجب أن تكون نفسها التي يقرأ منها `nginx`.
   ```cmd
   mkdir -p /home/vendors/staticfiles /home/vendors/media
   chown -R 1000:1000 /home/vendors/staticfiles /home/vendors/media
   ```

3. **تشغيل حاوية المشروع (Docker Container) مع bind mounts:**
   عند التشغيل، ستقوم الحاوية (عبر ملف `entrypoint.sh` 📜) بتطبيق تهجير قاعدة البيانات وتجميع ملفات الاستايل تلقائياً داخل المسارات المركبة، ثم تشغيل الخادم بواسطة `Daphne` 🐎.
   ```cmd
   docker run -d -p 8000:8000 \
     --name vendor-container \
     -v /home/vendors/staticfiles:/vol/web/static \
     -v /home/vendors/media:/vol/web/media \
     vendor-app
   ```

4. **تأكد أن `nginx` يقرأ من نفس المسارات على الخادم:**
   ```nginx
   location /static/ {
       alias /home/vendors/staticfiles/;
   }

   location /media/ {
       alias /home/vendors/media/;
   }
   ```

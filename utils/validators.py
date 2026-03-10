
class SyrianPhoneValidator:
    def __call__(self, value):
        if not re.match(r'^\+963\d{9}$', value):
            raise ValidationError('يجب أن يبدأ رقم الهاتف بـ +963 ويتبعه 9 أرقام.')

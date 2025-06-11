import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_("The password must contain at least one uppercase letter."))
        if not re.search(r'[0-9]', password):
            raise ValidationError(_("The password must contain at least one number."))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_("The password must contain at least one special character."))

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter, one number, and one special character.")

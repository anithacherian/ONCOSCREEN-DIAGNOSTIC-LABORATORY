import re
from django.core.exceptions import ValidationError
#cmmon validator for registration,rest and change password
class CustomPasswordValidator:
    def validate(self, password, user=None):

        if not re.search(r'[A-Za-z]', password):
            raise ValidationError(
                "Password must contain at least one letter."
            )

        if not re.search(r'\d', password):
            raise ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password must contain at least one special character."
            )

    def get_help_text(self):
        return (
            "Password must contain at least 8 characters, "
            "one letter, one number, and one special character."
        )

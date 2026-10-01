from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm

User = get_user_model()


class SignupForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "First name", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={"placeholder": "Last name", "autocomplete": "family-name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Work email", "autocomplete": "email"}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1", "")
        p2 = self.cleaned_data.get("password2", "")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"].lower()
        user.email = self.cleaned_data["email"].lower()
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # requires email confirmation
        if commit:
            user.save()
        return user


class PremiumAuthForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Your email", "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Your password", "autocomplete": "current-password"}),
    )


class PremiumPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"placeholder": "The email you signed up with", "autocomplete": "email"}),
    )


class PremiumSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"placeholder": "Choose a new password", "autocomplete": "new-password"}),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"placeholder": "Repeat the new password", "autocomplete": "new-password"}),
    )

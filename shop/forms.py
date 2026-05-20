from django import forms
from .models import Order, Comment
from django.contrib.auth.models import User

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'phone', 'address']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'phone': 'Телефон',
            'address': 'Адрес доставки',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '+375 (XX) XXX-XX-XX'}),
            'address': forms.TextInput(attrs={'placeholder': 'Город, улица, дом, квартира'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Поделитесь впечатлениями о парфюме...'
            }),
            'rating': forms.RadioSelect(
                choices=[(i, str(i)) for i in range(1, 6)],
                attrs={'class': 'star-rating-input'}
            ),
        }


class UserProfileForm(forms.ModelForm):
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Мобильный телефон",
        widget=forms.TextInput(attrs={'placeholder': '+375 (XX) XXX-XX-XX'})
    )
    
    address = forms.CharField(
        max_length=255, 
        required=False, 
        label="Адрес доставки (основной)",
        widget=forms.TextInput(attrs={'placeholder': 'Город, улица, дом, квартира'})
    )

    new_password = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Введите новый пароль, если хотите изменить'}),
        required=False
    )
    confirm_password = forms.CharField(
        label='Подтвердите новый пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Повторите новый пароль'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            if self.instance.profile.phone:
                self.fields['phone'].initial = self.instance.profile.phone
            if self.instance.profile.address:
                self.fields['address'].initial = self.instance.profile.address
            
    
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password or confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password', "Пароли не совпадают.")
            if new_password and len(new_password) < 8:
                self.add_error('new_password', "Пароль должен быть не менее 8 символов.")
        return cleaned_data
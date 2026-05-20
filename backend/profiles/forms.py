from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

from profiles.models import Profile


class PersonForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'country']
        widgets = {
            'country': CountrySelectWidget(),
        }

from django.forms import ModelForm, FileInput, TextInput
from .models import *

class PfpForm(ModelForm):
    class Meta:
        model = Utente
        fields = ["pfp"]
        widgets = {
            "pfp": FileInput(attrs={"class":"hide",
                                    "accept":"image/*",
                                    "onchange":"form.submit()"})
        }

class CoverForm(ModelForm):
    class Meta:
        model = Playlist
        fields = ["cover"]
        widgets = {
            "cover": FileInput(attrs={"class":"hide",
                                    "accept":"image/*",
                                    "onchange":"form.submit()"})
        }

from django.forms import ModelForm, FileInput
from .models import *

class ImageForm(ModelForm):
    class Meta:
        model = Utente
        fields = ["pfp"]
        widgets = {
            "pfp": FileInput(attrs={"class":"hide",
                                    "accept":"image/*",
                                    "onchange":"form.submit()"})
        }

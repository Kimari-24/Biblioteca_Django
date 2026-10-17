from django import forms


class BookForm(forms.Form):
    title = forms.CharField(label='Título', max_length=150)
    author = forms.CharField(label='Autor', max_length=100)
    category = forms.CharField(label='Categoría', max_length=50)
    isbn = forms.CharField(label='ISBN', max_length=20, required=False)
    copies = forms.IntegerField(label='Copias totales', min_value=1, max_value=99, initial=1)

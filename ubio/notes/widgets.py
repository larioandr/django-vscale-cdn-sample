from django.forms import FileInput


class CustomFileInput(FileInput):
    template_name = 'notes/widgets/file_input.html'
    accept = ''
    show_file_name = True

def can_edit(request, note):
    return note.owner.pk == request.user.pk

def can_delete(request, note):
    return note.owner.pk == request.user.pk

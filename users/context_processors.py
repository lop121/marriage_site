from users.models import Marriage


def get_marriage(request):
    marriagies = Marriage.objects.all()
    return {'marriagies': marriagies}
from users.models import Marriage


def get_marriage(request):
    marriages = Marriage.objects.filter(status = Marriage.Status.ACTIVE)
    return {'marriages': marriages}
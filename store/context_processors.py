from .models import UserLocation


def user_location(request):
    user_id = request.session.get("user_id")
    if user_id:
        try:
            from .models import CustomUser

            user = CustomUser.objects.get(id=user_id)
            loc = UserLocation.objects.get(user=user)
            return {"user_location": loc, "logged_in_user": user}
        except Exception:
            pass
    return {}

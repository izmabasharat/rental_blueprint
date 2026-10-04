from django.utils.functional import SimpleLazyObject


def favorites(request):
    """Makes `favorite_ids` available in every template ({% if l.pk in favorite_ids %}). Lazy: only queries if used."""
    def load():
        if not request.user.is_authenticated:
            return set()
        return set(request.user.favorites.values_list("listing_id", flat=True))
    return {"favorite_ids": SimpleLazyObject(load)}

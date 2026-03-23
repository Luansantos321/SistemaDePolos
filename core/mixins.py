class RestritoAoPoloMixin:
    """Mixin para views que filtram objetos pelo polo do usuário."""
    def get_queryset(self):
        qs = super().get_queryset()
        polo = getattr(self.request, 'polo', None)
        if polo:
            qs = qs.filter(polo=polo)
        return qs

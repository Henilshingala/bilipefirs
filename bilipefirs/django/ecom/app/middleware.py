class DiscountSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'session'):
            current_url = request.path
            last_url = request.session.get('last_url')

            if last_url and (
                (last_url == '/checkout/' and current_url != '/checkout/') or
                (current_url != '/checkout/' and 'discount_code' in request.session)
            ):
                request.session.pop('discount_percentage', None)
                request.session.pop('discount_code', None)
                request.session.modified = True

            request.session['last_url'] = current_url

        response = self.get_response(request)
        return response
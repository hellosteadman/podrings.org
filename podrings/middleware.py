def is_ajax_middleware(get_response):
    def middleware(request):
        requested_with = request.headers.get('X-Requested-With')
        display_as = request.headers.get('X-Display-As')
        
        request.is_ajax = requested_with == 'XMLHttpRequest'
        request.is_modal = display_as == 'modal'

        return get_response(request)

    return middleware

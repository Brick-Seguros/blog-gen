
def auth_middleware(request):
    api_key = request.headers.get('x-api-key')

    # Ensure API key is provided
    if not api_key:
        return {
            'shoudl_continue': False,
            'message': 'API key is missing',
            'status': 401
        }

    if api_key != "API_KEY":
        return {
            'shoudl_continue': False,
            'message': 'Invalid API key',
            'status': 403
        }

    return {
        'shoudl_continue': True
    }

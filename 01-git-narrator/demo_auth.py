def rotate_refresh_token(user_id: str) -> str:
    """
    Invalidates the current refresh token and issues a new one.
    Prevents token reuse attacks.
    """
    old_token = get_refresh_token(user_id)
    revoke_token(old_token)
    new_token = generate_secure_token()
    store_refresh_token(user_id, new_token)
    return new_token

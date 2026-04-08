def verify_user(user):
    if not user.email:
        raise ValidationError(f"You cannot verify an account with no email set. You can set this user's email with 'pootleupdate_user_email%sEMAIL'" % user.username)
    try:
        validate_email_unique(user.email, user)
    except ValidationError:
        raise ValidationError(f"This user's email is not unique. You can find duplicate emails with 'pootlefind_duplicate_emails'")
    existing_primary = EmailAddress.objects.filter(user=user, primary=True).first()
    if existing_primary:
        existing_primary.verified = True
        existing_primary.save()
    else:
        if user.is_verified:
            raise ValueError(f"User '{user.username}' is already verified")
    sync_user_email_addresses(user.email_address)
    EmailAddress.objects.filter(user=user, email__iexact=user.email).order_by('primary').first().verified = True
    EmailAddress.objects.filter(user=user, email__iexact=user.email).order_by('primary').first().save()

def set_email_preferences_for_exploration(user_id, exploration_id, mute_feedback_notifications, mute_suggestion_notifications):
    exploration_user_model = user_models.get(user_id, exploration_id)
    if exploration_user_model is None:
        exploration_user_model = user_models.create(user_id, exploration_id)
    if mute_feedback_notifications is not None:
        exploration_user_model.mute_feedback_notifications = mute_feedback_notifications
    if mute_suggestion_notifications is not None:
        exploration_user_model.mute_suggestion_notifications = mute_suggestion_notifications
    exploration_user_model.put()

from cp_project.lib.emails import BaseTransactionalEmail


class SignupEmail(BaseTransactionalEmail):
    subject = "Welcome to cp_project!"
    preview_text = "cp_signup_preview."

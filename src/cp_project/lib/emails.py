import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from smtplib import SMTPException
from typing import Literal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from pyutilkit.date_utils import now

from cp_project.accounts.models import User

CAPITAL_SPLIT = re.compile("[A-Z][^A-Z]*")
PREVIEW_LENGTH = 300
SUFFIXES = {"html": "html", "plain": "txt"}


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Attachment:
    name: str
    content: bytes
    mimetype: str


class BaseTransactionalEmail:
    subject: str
    preview_text: str

    @classmethod
    def get_template_name(cls) -> str:
        parts = re.findall(CAPITAL_SPLIT, cls.__name__)
        return "_".join(part.lower() for part in parts[:-1])

    @classmethod
    def get_template(cls, component: Literal["html", "plain"]) -> Template:
        suffix = f".{SUFFIXES[component]}.jinja"
        path = Path(component).joinpath(cls.get_template_name()).with_suffix(suffix)

        template_dir = settings.EMAIL_TEMPLATE_DIR.as_posix()
        env = Environment(  # noqa: S701
            loader=FileSystemLoader(template_dir), undefined=StrictUndefined
        )
        return env.get_template(path.as_posix())

    @classmethod
    def render_template(
        cls, template: Template, recipient: User, **kwargs: object
    ) -> str:
        kwargs.setdefault("recipient", recipient)
        kwargs.setdefault("current_year", now().year)
        return template.render(kwargs)

    @classmethod
    def plain_message(cls, recipient: User, **kwargs: object) -> str:
        return cls.render_template(cls.get_template("plain"), recipient, **kwargs)

    @classmethod
    def html_message(cls, recipient: User, **kwargs: object) -> str:
        return cls.render_template(
            cls.get_template("html"), recipient, preview_text=cls.preview_text, **kwargs
        )

    @classmethod
    def send_email(
        cls,
        recipient: User,
        attachments: Iterable[Attachment] = (),
        **kwargs: object,
    ) -> bool:
        mail = EmailMultiAlternatives(
            cls.subject,
            cls.plain_message(recipient, **kwargs),
            settings.NO_REPLY_EMAIL,
            [recipient.email],
            connection=get_connection(),
        )
        html_message = cls.html_message(recipient, **kwargs)
        mail.attach_alternative(html_message, "text/html")

        for attachment in attachments:
            mail.attach(attachment.name, attachment.content, attachment.mimetype)

        try:
            number_sent = mail.send()
        except SMTPException:
            success = False
        else:
            success = bool(number_sent)

        logger.info(
            "Attempted to sent %s to %s with subject (success: %s).",
            cls.__qualname__,
            recipient.email,
            success,
        )
        return success

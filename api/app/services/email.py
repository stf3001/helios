import logging

from app.core.config import settings

logger = logging.getLogger("helios.email")


async def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.frontend_url}/verifier-email?token={token}"
    if not settings.email_api_key:
        # Pas de fournisseur configuré (Resend/Brevo) : on logge le lien en dev
        # plutôt que d'échouer. À remplacer par un appel API réel avant la prod.
        logger.info("Email de vérification (mode dev, non envoyé) pour %s : %s", to, link)
        return
    # TODO(J9): appel API Resend/Brevo avec settings.email_api_key
    logger.info("Email de vérification pour %s : %s", to, link)

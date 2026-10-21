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


async def send_lead_notification(to: str | None, partner_name: str, lead_id) -> None:
    """Notifie un partenaire d'un nouveau lead (doc 08 §2 : TRANSMIS)."""
    msg = f"Nouveau lead HELIOS pour {partner_name} (#{lead_id}) — contact sous 5 jours ouvrés attendu."
    if not settings.email_api_key or not to:
        logger.info("Notification lead (mode dev, non envoyée) → %s : %s", to, msg)
        return
    # TODO(J9): appel API Resend/Brevo
    logger.info("Notification lead → %s : %s", to, msg)


async def send_rdv_notification(to: str | None, debut_paris: str, nom: str, telephone: str, sujet: str | None) -> None:
    """Annonce à l'équipe un rendez-vous téléphonique réservé (point 2 de TODO.md).

    PRÉPARÉ, PAS BRANCHÉ : sans fournisseur (`email_api_key`) ni destinataire
    (`rdv_notification_email`), une ligne de journal SANS nom ni téléphone — un journal
    n'est pas un endroit pour des données personnelles. Le contenu ci-dessous est celui qui
    partira quand le fournisseur sera choisi à la migration (Resend ou Brevo).
    """
    objet = f"Rendez-vous téléphonique — {debut_paris}"
    lignes = [
        f"{nom} a réservé un appel de 30 minutes le {debut_paris} (heure de Paris).",
        f"Numéro à appeler : {telephone}",
        *([f"Son sujet : {sujet}"] if sujet else []),
        "Le suivi se fait dans le back-office, page « Rendez-vous ».",
    ]
    corps = "\n".join(lignes)
    if not settings.email_api_key or not to:
        logger.info("Notification rendez-vous (non envoyée : fournisseur ou destinataire non configuré) — créneau %s",
                    debut_paris)
        return
    # TODO(J9): appel API Resend/Brevo avec settings.email_api_key, objet et corps ci-dessus
    logger.info("Notification rendez-vous → %s : %s (%d caractères)", to, objet, len(corps))

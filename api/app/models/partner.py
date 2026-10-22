import uuid
from datetime import date, datetime

from sqlalchemy import ARRAY, Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

# Cycle de vie d'un lead (doc 08 §2)
LEAD_STATUTS = ("nouveau", "transmis", "contacte", "devis", "signe", "perdu")


class Partner(Base):
    """Entreprise partenaire (apport d'affaires) — doc 08."""

    __tablename__ = "partners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raison_sociale: Mapped[str] = mapped_column(String(150), nullable=False)
    siret: Mapped[str | None] = mapped_column(String(14))
    email: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str | None] = mapped_column(String(255))  # défini à l'activation (accès espace partenaire)
    rge: Mapped[bool] = mapped_column(Boolean, default=False)
    zones: Mapped[list[str] | None] = mapped_column(ARRAY(String))    # codes postaux / départements couverts
    metiers: Mapped[list[str] | None] = mapped_column(ARRAY(String))  # pv, pac, isolation, menuiseries, vmc...
    charte_signee_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="candidat")  # candidat|actif|suspendu|refuse
    note_moyenne: Mapped[float | None] = mapped_column(Float)
    # Affiché au foyer à côté du nom (mises en relation, lot 1) : Hydrolia et Eolia sont des
    # sociétés du fondateur d'Hélios. Facultatif.
    lien_interet: Mapped[str | None] = mapped_column(String(200))
    # Partenaire de démonstration (point 60) : visible des seuls comptes de `mer_comptes_demo`.
    demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # Version de la charte signée dans l'espace partenaire (lot 3) ; `charte_signee_at` en est l'horodatage.
    charte_version_signee: Mapped[str | None] = mapped_column(String(20))
    motif_refus: Mapped[str | None] = mapped_column(Text)  # candidature refusée (statut `refuse`)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Lead(Base):
    """Mise en relation client ↔ partenaire — doc 08 §2. Immuable après SIGNÉ (traçabilité commission)."""

    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    house_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("houses.id"), nullable=False, index=True)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False, index=True)
    audit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("audits.id"))
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="travaux")  # travaux|energie (doc 09)
    metier: Mapped[str | None] = mapped_column(String(30))  # pv, pac, isolation... — sert au calcul de commission
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="nouveau")
    consent_client_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # consentement horodaté
    consent_retire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    montant_travaux: Mapped[int | None] = mapped_column(Integer)  # HT, renseigné à DEVIS/SIGNÉ
    commission: Mapped[float | None] = mapped_column(Numeric(10, 2))  # historique : plus calculée sur `travaux`
    # Prix fixe payé par le partenaire, figé à la création (`mer_prix_ht_eur`, 22/10/2026).
    prix_ht: Mapped[float | None] = mapped_column(Numeric(10, 2))
    # Le dossier transmis (lot 2) : instantané de ce que le foyer a COCHÉ, figé au consentement.
    # Retirer le consentement efface dossier, coordonnées, message, créneaux et copies de documents.
    dossier: Mapped[dict | None] = mapped_column(JSONB)
    score: Mapped[int | None] = mapped_column(Integer)          # 0-100, calculé ; ne change pas le prix
    score_detail: Mapped[list | None] = mapped_column(JSONB)    # [{critere, points, acquis}]
    creneaux: Mapped[list | None] = mapped_column(JSONB)        # [{"jour": "lundi", "plage": "matin"}]
    contact_nom: Mapped[str | None] = mapped_column(String(120))
    contact_telephone: Mapped[str | None] = mapped_column(String(30))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str | None] = mapped_column(Text)
    motif_perdu: Mapped[str | None] = mapped_column(Text)
    # Lot 3 : seule une contestation ACCEPTÉE passe un lead à non facturable ; le suivi déclaratif
    # du partenaire (dont `contacte_le`) ne touche jamais au prix.
    facturable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    contacte_le: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Review(Base):
    """Notation post-chantier du partenaire par le client — doc 08 §2/§4."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, unique=True)
    note: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    commentaire: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Contestation(Base):
    """Contestation d'une mise en relation par le partenaire, dans les 7 jours (lot 3)."""

    __tablename__ = "contestations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"),
                                               nullable=False, index=True)
    motif: Mapped[str] = mapped_column(String(30), nullable=False)
    commentaire: Mapped[str] = mapped_column(Text, nullable=False)
    essais: Mapped[list | None] = mapped_column(JSONB)  # dates ISO des trois essais (« injoignable »)
    statut: Mapped[str] = mapped_column(String(12), nullable=False, default="en_attente")
    decision_motif: Mapped[str | None] = mapped_column(Text)
    decidee_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class PartnerDocument(Base):
    """Justificatif d'un partenaire : `kbis`, `decennale`, `rge` (lot 3)."""

    __tablename__ = "partner_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"),
                                                  nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(12), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    date_delivrance: Mapped[date | None] = mapped_column(Date)  # Kbis
    date_fin: Mapped[date | None] = mapped_column(Date)         # décennale, RGE
    statut: Mapped[str] = mapped_column(String(10), nullable=False, default="depose")  # depose | refuse
    motif_refus: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Charte(Base):
    """Texte de la charte partenaire par version. La version en vigueur est la plus récente."""

    __tablename__ = "chartes"

    version: Mapped[str] = mapped_column(String(20), primary_key=True)
    texte: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class PartnerActivation(Base):
    """Lien d'activation à usage unique : seul le haché du jeton est stocké."""

    __tablename__ = "partner_activations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"),
                                                  nullable=False, index=True)
    jeton_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expire_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    utilise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class ReleveCloture(Base):
    """La clôture d'un mois de relevés (lot 4) — une ligne par mois, même vide."""

    __tablename__ = "releves_clotures"

    mois: Mapped[str] = mapped_column(String(7), primary_key=True)  # AAAA-MM, heure de Paris
    cloture_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    cloture_par: Mapped[str | None] = mapped_column(String(255))


class Releve(Base):
    """Relevé CLOS d'un partenaire pour un mois : instantané et PDF figés. Pas une facture."""

    __tablename__ = "releves"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False,
                                                  index=True)
    mois: Mapped[str] = mapped_column(String(7), ForeignKey("releves_clotures.mois"), nullable=False)
    statut: Mapped[str] = mapped_column(String(12), nullable=False, default="clos")
    instantane: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pdf_path: Mapped[str | None] = mapped_column(String(255))
    cloture_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

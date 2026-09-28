/**
 * Réserver 30 minutes au téléphone avec un conseiller — humain, cette fois.
 *
 * Sans compte : c'est une porte d'entrée, pas une récompense pour inscrits.
 *
 * Les créneaux viennent du serveur, jamais d'un calcul local : lui seul sait ce qui est
 * déjà pris, et lui seul décide de ses heures d'ouverture. Si deux visiteurs cliquent le
 * même créneau, le second reçoit un 409 et un message clair — la base porte un index
 * unique sur l'heure de début, c'est le seul verrou qui tienne.
 */

import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { CalendarClock, Check, Phone } from 'lucide-react'

interface Disponibilites {
  duree_min: number
  creneaux: string[]
}

const JOUR = new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })
const HEURE = new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' })

export default function RendezVousTel() {
  const [dispo, setDispo] = useState<Disponibilites | null>(null)
  const [jour, setJour] = useState<string | null>(null)
  const [creneau, setCreneau] = useState<string | null>(null)
  const [nom, setNom] = useState('')
  const [telephone, setTelephone] = useState('')
  const [email, setEmail] = useState('')
  const [sujet, setSujet] = useState('')
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState<string | null>(null)
  const [confirme, setConfirme] = useState<string | null>(null)

  const charger = () => {
    fetch('/api/rendez-vous/creneaux')
      .then((r) => (r.ok ? r.json() : null))
      .then((d: Disponibilites | null) => { if (d) setDispo(d) })
      .catch(() => { /* le bloc reste muet plutôt que d'afficher une panne */ })
  }

  useEffect(charger, [])

  /* Les créneaux rangés par journée : on choisit d'abord un jour, puis une heure. */
  const parJour = useMemo(() => {
    const groupes = new Map<string, string[]>()
    for (const iso of dispo?.creneaux ?? []) {
      const cle = iso.slice(0, 10)
      groupes.set(cle, [...(groupes.get(cle) ?? []), iso])
    }
    return groupes
  }, [dispo])

  const jours = [...parJour.keys()]
  const jourActif = jour && parJour.has(jour) ? jour : jours[0] ?? null
  const creneauxDuJour = jourActif ? parJour.get(jourActif) ?? [] : []

  async function reserver(e: FormEvent) {
    e.preventDefault()
    if (!creneau) return
    setEnvoi(true)
    setErreur(null)
    try {
      const reponse = await fetch('/api/rendez-vous', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          debut: creneau, nom, telephone,
          email: email.trim() || null, sujet: sujet.trim() || null,
        }),
      })
      if (reponse.ok) {
        setConfirme(creneau)
      } else {
        const corps = await reponse.json().catch(() => null)
        setErreur(corps?.detail ?? "La réservation n'a pas abouti. Réessayez dans un instant.")
        if (reponse.status === 409) { setCreneau(null); charger() }
      }
    } catch {
      setErreur("La réservation n'a pas abouti. Réessayez dans un instant.")
    } finally {
      setEnvoi(false)
    }
  }

  if (confirme) {
    const d = new Date(confirme)
    return (
      <div className="rounded-2xl border-2 border-leaf bg-leaf/5 p-6">
        <p className="flex items-start gap-3 font-display text-lg font-bold text-ink">
          <Check className="mt-0.5 h-6 w-6 shrink-0 text-leaf" />
          C’est noté : {JOUR.format(d)} à {HEURE.format(d)}.
        </p>
        <p className="mt-2 text-dark/80">
          Un conseiller vous appellera au <strong>{telephone}</strong>, pour une trentaine
          de minutes. Si vous ne pouvez plus, écrivez-nous — le créneau repartira à
          quelqu’un d’autre.
        </p>
      </div>
    )
  }

  if (!dispo || jours.length === 0) {
    return (
      <div className="rounded-2xl border border-ink/10 bg-white p-6 text-dark/70">
        <p className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-primary" />
          {dispo ? 'Aucun créneau disponible pour l’instant — revenez dans quelques jours.'
                 : 'Chargement des créneaux…'}
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={reserver} className="rounded-2xl border border-ink/10 bg-white p-5 sm:p-6">
      <p className="text-sm font-semibold uppercase tracking-wide text-primary">
        Choisissez un jour
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {jours.map((j) => (
          <button key={j} type="button"
            onClick={() => { setJour(j); setCreneau(null) }}
            aria-pressed={j === jourActif}
            className={`rounded-full border px-3 py-1.5 text-sm font-semibold transition
              ${j === jourActif ? 'border-primary bg-primary text-white'
                                : 'border-ink/20 text-ink hover:border-primary'}`}>
            {JOUR.format(new Date(`${j}T12:00:00`))}
          </button>
        ))}
      </div>

      <p className="mt-5 text-sm font-semibold uppercase tracking-wide text-primary">
        Puis une heure ({dispo.duree_min} minutes)
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {creneauxDuJour.map((iso) => (
          <button key={iso} type="button" onClick={() => setCreneau(iso)}
            aria-pressed={iso === creneau}
            className={`rounded-lg border px-3 py-1.5 text-sm font-semibold tabular-nums transition
              ${iso === creneau ? 'border-primary bg-primary text-white'
                                : 'border-ink/20 text-ink hover:border-primary'}`}>
            {HEURE.format(new Date(iso))}
          </button>
        ))}
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="block text-sm font-semibold text-ink">Votre nom</span>
          <input required value={nom} onChange={(e) => setNom(e.target.value)}
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2
              focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
        </label>
        <label className="block">
          <span className="block text-sm font-semibold text-ink">Votre téléphone</span>
          <input required type="tel" value={telephone} onChange={(e) => setTelephone(e.target.value)}
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2
              focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
        </label>
        <label className="block sm:col-span-2">
          <span className="block text-sm font-semibold text-ink">
            Votre e-mail <span className="font-normal text-dark/60">— facultatif</span>
          </span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2
              focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
        </label>
        <label className="block sm:col-span-2">
          <span className="block text-sm font-semibold text-ink">
            De quoi voulez-vous parler ? <span className="font-normal text-dark/60">— facultatif</span>
          </span>
          <textarea rows={2} value={sujet} onChange={(e) => setSujet(e.target.value)}
            placeholder="Un devis à relire, un projet solaire, une facture qui a grimpé…"
            className="mt-1 w-full rounded-lg border border-ink/20 px-3 py-2
              focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30" />
        </label>
      </div>

      {erreur && (
        <p className="mt-3 rounded-lg border border-terra/40 bg-terra/10 px-3 py-2 text-sm text-ink">
          {erreur}
        </p>
      )}

      <button type="submit" disabled={!creneau || envoi}
        className="mt-4 inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 font-semibold
          text-white transition hover:bg-primary/90 disabled:opacity-50">
        <Phone className="h-5 w-5" />
        {envoi ? 'Réservation…'
               : creneau ? `Réserver le ${JOUR.format(new Date(creneau))} à ${HEURE.format(new Date(creneau))}`
                         : 'Choisissez d’abord un créneau'}
      </button>
      <p className="mt-2 text-sm text-dark/60">
        Gratuit et sans engagement. Vos coordonnées servent à cet appel, et à rien d’autre.
      </p>
    </form>
  )
}

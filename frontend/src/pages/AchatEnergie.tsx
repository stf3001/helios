/**
 * « L'achat d'énergie » — la page chapeau du contrat d'électricité.
 *
 * PAS DE CALCULATEUR ICI. Le chiffrage d'un changement d'offre vit dans l'espace
 * connecté (`/espace/energie`), parce qu'il demande la consommation, la puissance
 * souscrite et l'option tarifaire réelles — trois choses qu'on ne devine pas. Cette
 * page explique, et renvoie.
 *
 * LE PARTI PRIS : on dit qui paie qui. Le courtage est un service utile, et il est
 * rémunéré par le fournisseur retenu — donc par une commission incluse dans le prix
 * du kWh. Le taire serait plus vendeur ; la charte (doc 01 : transparence, honnêteté)
 * dit l'inverse, et c'est ce qui donne du poids au reste de la page.
 *
 * Les prix sont DATÉS et renvoient à leur source. Une grille tarifaire change deux fois
 * par an : ce qui doit rester vrai, c'est l'explication, pas le chiffre.
 */

import { Link } from 'react-router-dom'
import {
  ArrowRight, BadgeCheck, CalendarDays, Clock, ExternalLink, Handshake,
  Lock, Scale, ShieldAlert, Sun, TrendingUp,
} from 'lucide-react'

import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useAuth } from '../context/AuthContext'
import { useTitle } from '../hooks/useTitle'

const COMPARATEUR = 'https://comparateur.energie-info.fr'

/** Les trois options du tarif réglementé. Le critère de choix, c'est vous, pas le prix. */
const OPTIONS = [
  {
    icon: Clock, nom: 'Base',
    resume: 'Le même prix à toute heure.',
    pour: 'Vous consommez surtout le soir et vous ne pouvez rien décaler.',
    texte: 'C’est l’option la plus simple, et souvent la plus juste quand la vie de la maison ne se plie pas à un programmateur. Abonnement moins cher que les autres options, aucun calcul à faire.',
  },
  {
    icon: CalendarDays, nom: 'Heures pleines / heures creuses',
    resume: 'Huit heures par jour à prix réduit.',
    pour: 'Un ballon d’eau chaude, un lave-linge ou une voiture peuvent tourner pendant ces heures-là.',
    texte: 'L’abonnement est un peu plus élevé : il faut donc déplacer vraiment de la consommation pour y gagner. Dès qu’un ballon d’eau chaude est programmable, le calcul penche en général de ce côté.',
  },
  {
    icon: TrendingUp, nom: 'Tempo',
    resume: '300 jours bleus, 43 blancs, 22 rouges.',
    pour: 'Vous pouvez vraiment vous effacer 22 jours par an — typiquement un chauffage non électrique.',
    texte: 'Les jours rouges ne tombent qu’entre novembre et mars, jamais le dimanche, et la couleur du lendemain est annoncée la veille. L’écart est considérable, dans les deux sens : Tempo récompense ceux qui s’effacent et punit sévèrement les autres.',
  },
]

/** Les formes de prix. Aucune n'est meilleure : elles répartissent le risque autrement. */
const FORMES = [
  {
    icon: Lock, nom: 'Prix fixe, ou « bloqué »',
    texte: 'Le prix du kWh est gelé pour un, deux ou trois ans. Vous achetez de la tranquillité : protégé d’une flambée, vous ne profitez pas d’une baisse.',
    risque: 'Le risque est pour le fournisseur.',
  },
  {
    icon: Scale, nom: 'Prix indexé',
    texte: 'Le prix suit une référence — le plus souvent le tarif réglementé — avec une remise en pourcentage. Vous suivez le marché à la hausse comme à la baisse.',
    risque: 'Le risque est partagé.',
  },
  {
    icon: TrendingUp, nom: 'Prix dynamique',
    texte: 'Le prix change chaque heure en suivant le marché de gros. Certaines heures ne coûtent presque rien, voire passent en négatif quand le solaire national déborde. D’autres coûtent très cher.',
    risque: 'Le risque est pour vous — et le gain aussi.',
  },
]

export default function AchatEnergie() {
  useTitle('L’achat d’énergie — abonnements, tarifs et courtage | HELIOS')
  const { user } = useAuth()

  return (
    <>
      <Hero
        title="L’achat d’énergie"
        subtitle="Produire moins cher, c’est une moitié du sujet. Acheter moins cher ce qu’on produit pas, c’est l’autre — et elle ne coûte rien à mettre en œuvre."
      />

      <section className="mx-auto max-w-[1100px] px-4 py-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Votre facture se joue sur deux lignes
        </h2>
        <p className="mt-3 max-w-[820px] text-lg text-dark/80">
          L’abonnement, qui dépend de votre puissance souscrite, et le prix du kWh, qui
          dépend de votre option tarifaire et de votre offre. Poser des panneaux agit sur
          la quantité achetée ; choisir son contrat agit sur le prix de chaque kWh restant.
          Les deux se cumulent, et le second est <strong className="text-ink">gratuit</strong> :
          changer de fournisseur ne coûte rien, ne coupe rien, et ne demande aucune
          intervention technique.
        </p>
      </section>

      {/* Les options du tarif réglementé. */}
      <section className="bg-cream py-12">
        <div className="mx-auto max-w-[1100px] px-4">
          <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
            Base, heures creuses ou Tempo ?
          </h2>
          <p className="mt-3 max-w-[820px] text-dark/80">
            Ce sont trois options du même tarif réglementé. Le critère de choix n’est pas
            le prix affiché : c’est votre capacité à déplacer une consommation. Un même
            foyer peut gagner ou perdre plusieurs centaines d’euros par an selon l’option,
            à consommation identique.
          </p>
          <div className="mt-6 grid gap-5 md:grid-cols-3">
            {OPTIONS.map((o) => (
              <div key={o.nom} className="flex flex-col rounded-2xl border border-ink/10 bg-white p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                  <o.icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mt-3 font-display text-lg font-bold text-ink">{o.nom}</h3>
                <p className="mt-1 font-semibold text-primary">{o.resume}</p>
                <p className="mt-2 text-dark/75">{o.texte}</p>
                <p className="mt-3 border-t border-ink/10 pt-3 text-sm text-dark/70">
                  <strong className="text-ink">Pour qui :</strong> {o.pour}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-sm text-dark/70">
            Sur la grille Tempo en vigueur au 1<sup>er</sup> août 2026, le kWh va de
            0,1356 € en heures creuses bleues à 0,7295 € en heures pleines rouges — plus de
            cinq fois plus cher. Ces montants changent deux fois par an ;
            le raisonnement, lui, ne change pas.
          </p>
        </div>
      </section>

      {/* La réforme des heures creuses : personne ne la connaît, elle concerne tout le monde. */}
      <section className="mx-auto max-w-[1100px] px-4 py-12">
        <div className="rounded-2xl border-2 border-primary bg-white p-6 sm:p-8">
          <div className="flex items-start gap-3">
            <Sun className="mt-1 h-6 w-6 shrink-0 text-primary" />
            <div>
              <h2 className="font-display text-2xl font-bold text-ink">
                Vos heures creuses vont changer d’horaire
              </h2>
              <p className="mt-3 max-w-[820px] text-lg text-dark/80">
                C’est en cours et presque personne ne le sait. Depuis novembre 2025, Enedis
                applique une réforme décidée par la Commission de régulation de l’énergie :
                les heures creuses du matin et du début de soirée disparaissent
                progressivement, remplacées par au moins cinq heures consécutives la nuit
                et <strong className="text-ink">jusqu’à trois heures l’après-midi</strong>,
                entre 11 h et 17 h.
              </p>
              <p className="mt-3 max-w-[820px] text-dark/80">
                La deuxième vague concerne 9,3 millions de foyers, étalée jusqu’à l’automne
                2027, et les horaires pourront devenir saisonniers : des heures creuses
                l’après-midi en été, entièrement nocturnes en hiver. Le changement se fait à
                distance sur le compteur Linky, et vous en êtes prévenu.
              </p>
              <div className="mt-5 rounded-xl bg-cream p-4">
                <p className="font-semibold text-ink">Deux choses à retenir</p>
                <ul className="mt-2 space-y-2 text-dark/80">
                  <li>
                    <strong className="text-ink">Le jour où vos horaires changent,
                    reprogrammez votre ballon d’eau chaude et votre voiture.</strong> Sans
                    cela vous chaufferez en heures pleines sans vous en apercevoir, et la
                    facture montera sans explication.
                  </li>
                  <li>
                    <strong className="text-ink">Pour une maison solaire, c’est une bonne
                    nouvelle.</strong> Des heures creuses en milieu de journée tombent
                    exactement quand vos panneaux produisent : vous chauffez votre eau au
                    meilleur moment, que ce soit avec votre production ou au tarif réduit.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Les formes de prix. */}
      <section className="mx-auto max-w-[1100px] px-4 pb-12">
        <h2 className="font-display text-2xl font-bold text-ink md:text-3xl">
          Bloquer son prix, le suivre, ou en profiter heure par heure
        </h2>
        <p className="mt-3 max-w-[820px] text-dark/80">
          Au-delà de l’option tarifaire, une offre a une forme de prix. Aucune n’est
          meilleure en soi : elles répartissent simplement le risque autrement entre vous
          et le fournisseur.
        </p>
        <div className="mt-6 grid gap-5 md:grid-cols-3">
          {FORMES.map((f) => (
            <div key={f.nom} className="rounded-2xl border border-ink/10 bg-white p-5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <f.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-3 font-display text-lg font-bold text-ink">{f.nom}</h3>
              <p className="mt-1.5 text-dark/75">{f.texte}</p>
              <p className="mt-3 text-sm font-semibold text-primary">{f.risque}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 max-w-[820px] text-dark/80">
          Personne ne sait où seront les prix dans deux ans, et un commercial qui vous
          l’affirme vous vend sa conviction, pas une information. La question utile est
          ailleurs : une hausse de 20 % sur votre facture, est-ce un ennui ou un problème ?
          Si c’est un problème, bloquez. Si c’est un ennui, le tarif réglementé fait très
          bien l’affaire.
        </p>
      </section>

      {/* SOBRY : le tarif dynamique, nommé. Partenaire, et dit comme tel. */}
      <section className="mx-auto max-w-[1100px] px-4 pb-12">
        <div className="rounded-2xl border border-ink/10 bg-white p-6 sm:p-8">
          <h2 className="font-display text-2xl font-bold text-ink">
            SOBRY, le tarif dynamique que nous connaissons
          </h2>
          <p className="mt-3 max-w-[820px] text-lg text-dark/80">
            SOBRY est un fournisseur français dont le prix du kWh suit le marché de gros
            heure par heure. Sa particularité tient en une phrase :
            <strong className="text-ink"> aucune marge sur le kWh</strong> — il se
            rémunère uniquement sur l’abonnement fixe. Les prix du lendemain sont publiés
            chaque jour, sans engagement, avec un compteur Linky.
          </p>
          <div className="mt-6 grid gap-5 md:grid-cols-2">
            <div className="rounded-xl bg-cream p-5">
              <p className="font-display text-lg font-bold text-ink">SoFlex</p>
              <p className="mt-2 text-dark/80">
                Le marché sans filet : les heures très bon marché comme les pointes.
                C’est l’offre qui laisse profiter des heures à prix négatif, quand la
                production solaire nationale dépasse la demande en milieu de journée.
              </p>
            </div>
            <div className="rounded-xl bg-cream p-5">
              <p className="font-display text-lg font-bold text-ink">SoCap</p>
              <p className="mt-2 text-dark/80">
                La même mécanique, mais plafonnée : vous renoncez aux prix négatifs en
                échange d’un prix maximum garanti. Moins de gain possible, et pas de
                mauvaise surprise en cas de flambée.
              </p>
            </div>
          </div>
          <p className="mt-5 max-w-[820px] text-dark/80">
            <strong className="text-ink">Ce n’est pas fait pour tout le monde</strong>, et
            nous préférons le dire avant : un tarif dynamique ne récompense que les foyers
            capables de déplacer des usages — ballon d’eau chaude, voiture, pompe à chaleur,
            batterie. Si vous ne pouvez rien décaler, vous subirez les pointes sans
            atteindre les creux.
          </p>
          <p className="mt-3 text-sm text-dark/60">
            SOBRY est partenaire d’HELIOS. Si nous vous proposons une étude, nous vous
            donnerons notre avis sur le résultat — y compris quand il est défavorable.
          </p>
        </div>
      </section>

      {/* Le courtage, et qui le paie. C'est le coeur honnête de la page. */}
      <section className="bg-ink py-12 text-white">
        <div className="mx-auto max-w-[1100px] px-4">
          <div className="flex items-start gap-3">
            <Handshake className="mt-1 h-6 w-6 shrink-0 text-sun" />
            <div>
              <h2 className="font-display text-2xl font-bold md:text-3xl">
                Le courtage : utile, et payé par quelqu’un
              </h2>
              <p className="mt-3 max-w-[820px] text-lg text-white/85">
                Un courtier compare les offres du marché à votre place, négocie, et vous
                présente les contrats qui collent à votre profil. C’est un vrai travail, et
                il fait gagner du temps. Avant de signer, il faut savoir comment il est
                rémunéré.
              </p>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl bg-white/10 p-5">
                  <p className="font-display text-lg font-bold">Qui paie le courtier</p>
                  <p className="mt-2 text-white/85">
                    Dans la grande majorité des cas, pas vous : le fournisseur retenu, sous
                    forme d’une commission incluse dans le prix du kWh. Ce n’est pas
                    illégitime, mais cela veut dire que sa rémunération dépend de l’offre
                    qu’il vous fait signer.
                  </p>
                </div>
                <div className="rounded-2xl bg-white/10 p-5">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-5 w-5 shrink-0 text-sun" />
                    <p className="font-display text-lg font-bold">Ce que la loi n’impose pas</p>
                  </div>
                  <p className="mt-2 text-white/85">
                    Le courtage en énergie est le seul courtage où aucune immatriculation
                    ORIAS n’est exigée, et où la transparence sur la rémunération n’est pas
                    une obligation légale. Un courtier sérieux vous remet donc de lui-même
                    un mandat écrit, non exclusif et limité dans le temps, qui dit comment
                    il est payé. Demandez-le : un refus est une réponse en soi.
                  </p>
                </div>
              </div>
              <div className="mt-6 flex flex-wrap items-center gap-4 rounded-2xl bg-white/10 p-5">
                <BadgeCheck className="h-6 w-6 shrink-0 text-sun" />
                <p className="min-w-[16rem] flex-1 text-white/90">
                  <strong className="text-white">Notre règle, et elle nous coûte de
                  l’argent :</strong> si l’économie estimée est inférieure à 5 %, nous vous
                  conseillons de ne rien changer. Un gain marginal ne justifie pas un
                  nouvel engagement. HELIOS ne vous facture jamais rien et ne touche aucune
                  commission de votre part.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* La demande de courtage : le service, et ce qu'il faut pour l'utiliser. */}
      <section className="mx-auto max-w-[1100px] px-4 py-12">
        <div className="rounded-2xl border border-ink/10 bg-white p-6 sm:p-8">
          <h2 className="font-display text-2xl font-bold text-ink">
            Faire étudier votre contrat
          </h2>
          <p className="mt-3 max-w-[820px] text-lg text-dark/80">
            Depuis votre espace, vous pouvez demander une étude de courtage auprès de notre
            partenaire. Vous renseignez votre fournisseur actuel, votre offre, votre
            consommation et votre puissance souscrite ; nous transmettons ce profil, et
            nous vous rendons le résultat avec notre avis — y compris quand cet avis est
            « restez où vous êtes ».
          </p>
          <ol className="mt-6 space-y-3">
            {[
              ['Vous créez votre espace', 'Il faut un compte, parce qu’une étude porte sur des informations personnelles et qu’elles n’ont rien à faire dans une page publique.'],
              ['Vous donnez votre consentement', 'Rien n’est transmis sans un accord explicite et horodaté. Vous voyez exactement ce qui part.'],
              ['Le partenaire étudie votre profil', 'Il compare les offres du marché sur votre consommation réelle, pas sur une moyenne.'],
              ['Helios vous rend le résultat, et son avis', 'Avec le lien vers le comparateur public, pour que vous puissiez vérifier sans nous.'],
            ].map(([titre, texte], i) => (
              <li key={titre} className="flex items-start gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full
                  bg-primary text-sm font-bold text-white">{i + 1}</span>
                <span className="text-dark/80">
                  <strong className="text-ink">{titre}</strong> — {texte}
                </span>
              </li>
            ))}
          </ol>

          <div className="mt-7 flex flex-wrap gap-3">
            {user ? (
              <Link to="/espace/energie"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3
                  font-semibold text-white transition hover:opacity-90">
                Demander une étude <ArrowRight className="h-5 w-5" />
              </Link>
            ) : (
              <Link to="/inscription"
                className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3
                  font-semibold text-white transition hover:opacity-90">
                Créer mon espace <ArrowRight className="h-5 w-5" />
              </Link>
            )}
            <a href={COMPARATEUR} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-ink/20 px-5 py-3
                font-semibold text-ink transition hover:border-primary hover:text-primary">
              Comparer seul, sur le comparateur public <ExternalLink className="h-4 w-4" />
            </a>
          </div>
          <p className="mt-3 text-sm text-dark/60">
            Le comparateur du Médiateur national de l’énergie est public, gratuit et
            indépendant — de nous comme de nos partenaires. Nous le citons à chaque fois,
            et ce n’est pas une politesse : c’est ce qui vous permet de vérifier ce qu’on
            vous raconte.
          </p>
        </div>
      </section>

      {/* Le lien avec le reste : l'achat n'a de sens qu'à côté de la production. */}
      <section className="mx-auto max-w-[1100px] px-4 pb-12">
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-cream p-6 sm:p-8">
          <p className="min-w-[18rem] flex-1 text-lg text-dark/80">
            L’option tarifaire se choisit sur la facture <em>qui vous restera</em>, pas sur
            celle d’aujourd’hui. Le simulateur la calcule heure par heure, sur votre adresse.
          </p>
          <Link to="/simulateur-solaire"
            className="inline-flex items-center gap-2 rounded-xl bg-ink px-5 py-3
              font-semibold text-white transition hover:opacity-90">
            Équiper ma maison <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-[1100px] px-4 pb-16">
        <FichesLiees cats={['achat_energie']} titre="Vos questions sur l’achat d’énergie" />
      </section>
    </>
  )
}

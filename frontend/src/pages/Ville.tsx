import { Link, useParams } from 'react-router-dom'
import { ArrowRight, MapPin, Sun } from 'lucide-react'
import Hero from '../components/Hero'
import FichesLiees from '../components/FichesLiees'
import { useTitle } from '../hooks/useTitle'
import villes from '../data/villes.json'

/** Ce que la zone climatique réglementaire implique concrètement — c'est ce qui rend la page
 *  utile localement, au-delà du seul chiffre de production. */
const ZONE_CONSEIL: Record<string, string> = {
  H1: "Zone climatique H1, la plus froide : les besoins de chauffage dominent largement la facture. L'isolation de la toiture reste donc le premier poste, avant toute production d'électricité.",
  H2: "Zone climatique H2, tempérée océanique : les besoins de chauffage restent significatifs, mais l'humidité rend la ventilation particulièrement importante à surveiller lors des travaux d'isolation.",
  H3: "Zone climatique H3, méditerranéenne : les besoins de chauffage sont plus faibles, et c'est le confort d'été qui devient le sujet principal — protections solaires et déphasage des isolants avant tout.",
}

export default function Ville() {
  const { slug } = useParams()
  const ville = villes.find((v) => v.slug === slug)

  useTitle(ville ? `Panneaux solaires à ${ville.nom}` : undefined)

  if (!ville) {
    return (
      <section className="max-w-[720px] mx-auto px-4 py-16 text-center text-gray-600">
        Ville inconnue. <Link to="/solaire" className="text-primary underline">Voir le guide solaire</Link>
      </section>
    )
  }

  return (
    <>
      <Hero
        title={`Panneaux solaires à ${ville.nom}`}
        subtitle={`Ce que produit réellement une toiture ${ville.nom.startsWith('A') ? "à" : "à"} ${ville.nom}, et ce que ça change pour votre projet.`}
      />

      <section className="max-w-[900px] mx-auto px-4 py-12">
        <p className="text-lg text-gray-700 leading-relaxed max-w-[68ch]">
          L'ensoleillement change tout : à production installée identique, une toiture ne fournit
          pas la même chose selon l'endroit. Les chiffres ci-dessous viennent de PVGIS, la base de
          données de la Commission européenne — ce ne sont pas des moyennes nationales.
        </p>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {[
            { kwc: 3, kwh: ville.prod_3kwc },
            { kwc: 6, kwh: ville.prod_6kwc },
            { kwc: 9, kwh: ville.prod_9kwc },
          ].map((p) => (
            <div key={p.kwc} className="rounded-2xl border border-gray-200 p-5 bg-white">
              <div className="flex items-center gap-2 text-primary text-sm font-semibold">
                <Sun className="w-4 h-4" /> Installation {p.kwc} kWc
              </div>
              <div className="text-3xl font-bold text-ink mt-2 tabular-nums">
                {p.kwh.toLocaleString('fr-FR')}
              </div>
              <div className="text-sm text-gray-500">kWh produits par an</div>
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-500 mt-3 max-w-[68ch]">
          Hypothèse : toiture orientée plein sud, inclinée à 30°, sans ombrage. Votre toiture
          diffère forcément — orientation, pente, arbres ou bâtiments voisins font varier ces
          chiffres, parfois beaucoup. Le simulateur calcule le cas réel à votre adresse.
        </p>
      </section>

      <section className="max-w-[900px] mx-auto px-4 pb-12">
        <div className="rounded-2xl bg-cream border border-black/5 p-6">
          <div className="flex items-center gap-2 text-ink font-semibold mb-2">
            <MapPin className="w-4 h-4 text-primary" /> Le contexte local
          </div>
          <p className="text-gray-700 leading-relaxed max-w-[68ch]">{ZONE_CONSEIL[ville.zone]}</p>
          <p className="text-gray-700 leading-relaxed max-w-[68ch] mt-3">
            Côté aides, au-delà des dispositifs nationaux, le département {ville.departement} et
            votre commune peuvent proposer leurs propres soutiens. Ils changent chaque année et ne
            sont pas centralisés : le simulateur officiel france-renov.gouv.fr les recense par code
            postal, et un Espace Conseil France Rénov' local vous les détaillera gratuitement.
          </p>
        </div>
      </section>

      <section className="max-w-[900px] mx-auto px-4 pb-12">
        <div className="flex flex-wrap gap-3">
          <Link
            to="/simulateur-solaire"
            className="inline-flex items-center gap-2 rounded-xl bg-primary text-white font-semibold px-4 py-2.5 hover:opacity-90"
          >
            Simuler ma toiture à {ville.nom} <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/solaire"
            className="inline-flex items-center gap-2 rounded-xl border border-gray-300 px-4 py-2.5 font-semibold text-ink hover:bg-gray-50"
          >
            Le guide solaire complet
          </Link>
        </div>
      </section>

      <section className="max-w-[900px] mx-auto px-4 pb-8">
        <h2 className="text-lg font-semibold text-ink mb-3">Autres villes</h2>
        <div className="flex flex-wrap gap-2">
          {villes
            .filter((v) => v.slug !== ville.slug)
            .map((v) => (
              <Link
                key={v.slug}
                to={`/solaire/${v.slug}`}
                className="rounded-full border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:border-primary hover:text-primary"
              >
                {v.nom}
              </Link>
            ))}
        </div>
      </section>

      <FichesLiees cats={['photovoltaique', 'autoconso']} titre="Les questions qu'on se pose avant d'installer" />
    </>
  )
}

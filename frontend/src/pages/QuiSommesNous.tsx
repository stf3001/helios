import { Link } from 'react-router-dom'
import { Bot, UserCheck, FileCheck2, Sprout } from 'lucide-react'
import ScrollReveal from '../components/ScrollReveal'
import CtaFaisTaPart from '../components/CtaFaisTaPart'
import { useTitle } from '../hooks/useTitle'

export default function QuiSommesNous() {
  useTitle('Qui sommes-nous')
  return (
    <>
      {/* Hero avec l'avatar Helios — une identité, pas qu'un dégradé */}
      <section className="relative overflow-hidden bg-gradient-to-br from-sun via-primary to-terra text-white">
        <div className="max-w-[1100px] mx-auto px-4 py-16 md:py-20 grid md:grid-cols-[1.3fr_1fr] gap-8 items-center">
          <div className="text-center md:text-left">
            <h1 className="font-display text-4xl md:text-5xl font-bold text-white leading-tight mb-4">Qui sommes-nous</h1>
            <p className="text-xl text-white/90">Une conviction simple, mise au service de chaque foyer.</p>
          </div>
          <div className="hidden md:flex justify-center">
            <img src="/brand/helios-thumbsup.png" alt="Helios" className="h-56 drop-shadow-xl" />
          </div>
        </div>
      </section>

      {/* Origine / mission */}
      <section className="max-w-[820px] mx-auto px-4 py-16 space-y-5 text-lg text-gray-700">
        <ScrollReveal>
          <p>
            HELIOS est né d'un constat frustrant : la transition énergétique de la maison est devenue un
            labyrinthe. Aides qui changent chaque année, démarchage agressif, devis incompréhensibles,
            conseils orientés par celui qui vend. Résultat : des millions de foyers renoncent, ou se
            trompent de travaux — alors que, pour la première fois, les solutions techniques existent
            vraiment.
          </p>
        </ScrollReveal>
        <ScrollReveal delay={80}>
          <p>
            Notre conviction : chacun devrait pouvoir avoir accès à un conseil <strong className="text-ink">
            honnête, personnalisé et disponible</strong> — sans avoir à démêler seul cent pages
            d'information contradictoire, et sans qu'un vendeur soit juge et partie.
          </p>
        </ScrollReveal>
      </section>

      {/* L'alliance humain + IA */}
      <section className="bg-cream py-16">
        <div className="max-w-[900px] mx-auto px-4">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-10">L'alliance de l'humain et de l'IA</h2>
          <div className="grid gap-5 sm:grid-cols-2">
            <ScrollReveal className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="w-11 h-11 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-3">
                <Bot className="w-6 h-6" />
              </div>
              <h3 className="font-display font-semibold text-ink mb-1">L'IA, pour la puissance et la disponibilité</h3>
              <p className="text-sm text-gray-600">
                Helios est disponible à toute heure, connaît les normes et les aides, et s'adapte à votre
                logement précis — sans jamais se fatiguer d'expliquer deux fois la même chose.
              </p>
            </ScrollReveal>
            <ScrollReveal delay={100} className="bg-white rounded-2xl border border-gray-200 p-6">
              <div className="w-11 h-11 rounded-xl bg-leaf/10 text-leaf flex items-center justify-center mb-3">
                <UserCheck className="w-6 h-6" />
              </div>
              <h3 className="font-display font-semibold text-ink mb-1">L'humain, pour le sens et le contrôle</h3>
              <p className="text-sm text-gray-600">
                Les chiffres viennent de moteurs de calcul vérifiés, jamais d'une IA qui invente. Les
                partenaires sont sélectionnés et suivis par une équipe, pas par un algorithme seul.
              </p>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* La constitution — preuve, pas promesse */}
      <section className="max-w-[900px] mx-auto px-4 py-16">
        <ScrollReveal className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-4">
            <FileCheck2 className="w-7 h-7" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-ink mb-3">Un engagement écrit, pas une promesse marketing</h2>
          <p className="text-gray-700 max-w-2xl">
            Nos règles ne sont pas qu'affichées sur cette page : elles sont écrites dans une
            « constitution » versionnée, et appliquées directement dans le code d'Helios. Un avis
            défavorable peut être rendu avant toute mise en relation. Un chiffre est toujours une
            fourchette. Un partenaire n'apparaît jamais si l'avis d'Helios est négatif.
          </p>
        </ScrollReveal>
        <ScrollReveal delay={80} className="text-center">
          <Link to="/engagements" className="inline-flex items-center gap-1.5 text-primary font-semibold hover:gap-2.5 transition-all">
            Découvrir tous nos engagements →
          </Link>
        </ScrollReveal>
      </section>

      {/* Ce qui nous anime */}
      <section className="bg-cream py-16">
        <div className="max-w-[820px] mx-auto px-4 text-center">
          <div className="w-14 h-14 rounded-2xl bg-leaf/10 text-leaf flex items-center justify-center mx-auto mb-4">
            <Sprout className="w-7 h-7" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold text-ink mb-4">Ce qui nous anime</h2>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto">
            Nous ne prétendons pas résoudre seuls la crise énergétique. Nous croyons simplement que
            chaque foyer bien conseillé, c'est un pas de plus — et que ce conseil ne devrait jamais
            dépendre du budget marketing de celui qui le donne.
          </p>
          <p className="font-display text-xl font-semibold text-ink mt-6">
            <Link to="/colibri" className="hover:text-primary transition-colors">« Je le sais, mais je fais ma part. »</Link>
          </p>
        </div>
      </section>

      <CtaFaisTaPart />
    </>
  )
}

export default function Hero({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <section className="relative py-16 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-sun via-primary to-terra" />
      <div className="relative z-10 max-w-[900px] mx-auto px-4 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">{title}</h1>
        {subtitle && <p className="text-xl text-white/90">{subtitle}</p>}
      </div>
    </section>
  )
}

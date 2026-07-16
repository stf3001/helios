import { useState } from 'react'
import Hero from '../components/Hero'
import { faq } from '../data/faq'
import { ChevronDown } from 'lucide-react'

export default function Faq() {
  const [open, setOpen] = useState<number | null>(null)
  return (
    <>
      <Hero title="Questions fréquentes" subtitle="Un aperçu — Helios en connaît bien plus." />
      <section className="max-w-[800px] mx-auto px-4 py-12 space-y-3">
        {faq.map((e, i) => (
          <div key={i} className="bg-gray-50 rounded-2xl">
            <button
              className="w-full flex items-center justify-between p-4 text-left font-semibold"
              onClick={() => setOpen(open === i ? null : i)}
            >
              <span><span className="text-primary text-xs mr-2 uppercase">{e.cat}</span>{e.q}</span>
              <ChevronDown className={`w-5 h-5 shrink-0 transition-transform ${open === i ? 'rotate-180' : ''}`} />
            </button>
            {open === i && <p className="px-4 pb-4 text-gray-700">{e.r}</p>}
          </div>
        ))}
      </section>
    </>
  )
}

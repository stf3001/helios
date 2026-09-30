import type { ReactNode } from 'react'

export default function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-bord rounded-2xl p-6 transition-colors hover:border-gray-300">
      <h3 className="font-display text-xl text-ink mb-2">{title}</h3>
      <div className="text-gray-600">{children}</div>
    </div>
  )
}

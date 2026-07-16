import type { ReactNode } from 'react'

export default function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-gray-50 rounded-2xl p-6 hover:bg-primary/5 transition-colors">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <div className="text-gray-700">{children}</div>
    </div>
  )
}

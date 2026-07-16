export type FieldOption = { value: string; label: string }

export type FieldSpec =
  | { key: string; label: string; type: 'select'; options: FieldOption[]; help?: string }
  | { key: string; label: string; type: 'multiselect'; options: FieldOption[]; help?: string }
  | { key: string; label: string; type: 'number'; min?: number; max?: number; help?: string }
  | { key: string; label: string; type: 'boolean'; help?: string }
  | { key: string; label: string; type: 'text'; help?: string }
  | { key: string; label: string; type: 'textarea'; help?: string }

export type FieldValue = string | number | boolean | string[] | null | undefined

export type Draft = Record<string, FieldValue>

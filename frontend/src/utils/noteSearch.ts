import type { Note } from '../stores/notes'

export function noteMatchesQuery(note: Note, raw: string): boolean {
  const q = raw.trim().toLowerCase()
  if (!q) return true
  const parts: string[] = [
    note.title,
    note.summary,
    note.authorUsername,
    note.authorNickname,
    ...(note.blocks?.map((b) => b.content) ?? []),
  ].filter((s): s is string => Boolean(s && String(s).trim()))
  const hay = parts.join('\n').toLowerCase()
  return hay.includes(q)
}

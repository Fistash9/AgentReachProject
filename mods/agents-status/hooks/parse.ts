// Чисті функції розбору — без $, щоб їх можна було перевірити тестом.

export type Node = { id: string; owner: string }

// Рядки дерева "- [>] ID назва … @агент" (вивід grep -h). Без @агент — власник "".
export function parseTree(stdout: string): Node[] {
  const out: Node[] = []
  for (const line of stdout.split('\n')) {
    const m = line.match(/^\s*- \[>\]\s+(\S+)/)
    if (!m) continue
    const owner = line.match(/@([\w-]+)\s*$/)
    out.push({ id: m[1], owner: owner ? owner[1] : '' })
  }
  return out
}

// Пункт «в роботі» (◐) зі списку задач на екрані DSH: "│   5 │ ◐  │ Текст… │".
export function parseDshTodo(screen: string): string | null {
  for (const line of screen.split('\n')) {
    if (!line.includes('◐')) continue
    const cells = line.split('│').map(c => c.trim()).filter(Boolean)
    const i = cells.indexOf('◐')
    if (i >= 0 && cells[i + 1]) return cells[i + 1]
  }
  return null
}

export function describe(nodes: Node[], todo: string | null, tmuxOk: boolean) {
  const mine = nodes.filter(n => n.owner !== 'dsh').map(n => n.id)
  const dsh = nodes.filter(n => n.owner === 'dsh').map(n => n.id)
  const tree = `Дерево: ${mine.join(', ') || '—'} · у DSH: ${dsh.join(', ') || '—'}`
  if (!tmuxOk) return { tree, dsh: 'DSH насправді: вікно work:3 не прочитано', isMismatch: false }
  if (todo === null) return { tree, dsh: 'DSH насправді: пункту ◐ на екрані нема', isMismatch: false }
  const isMismatch = dsh.length > 0 && !dsh.some(id => todo.includes(id))
  return { tree, dsh: `DSH насправді: ${todo}`, isMismatch }
}

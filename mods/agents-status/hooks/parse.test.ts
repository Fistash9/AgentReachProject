import { expect, test } from 'claude-code/testing'

import { describe, parseDshTodo, parseTree } from './parse'

test('дерево: свої й чужі [>]', () => {
  const nodes = parseTree('  - [>] T11 cases-v3\n- [ ] T12 інше\n    - [>] T7 щось @dsh\n- [>] Q12 реєстр @claude-code\n')
  expect(nodes).toEqual([
    { id: 'T11', owner: '' }, { id: 'T7', owner: 'dsh' }, { id: 'Q12', owner: 'claude-code' },
  ])
})

test('DSH: пункт ◐ зі списку задач', () => {
  const screen = '│   4 │ ☑  │ Чернетка патчу │\n│   5 │ ◐  │ Чекаю явного «так» на verify-nudge │\n'
  expect(parseDshTodo(screen)).toBe('Чекаю явного «так» на verify-nudge')
  expect(parseDshTodo('нічого')).toBe(null)
})

test('⚠, коли пункт DSH не згадує його вузол з дерева', () => {
  const nodes = [{ id: 'T11', owner: '' }, { id: 'T7', owner: 'dsh' }]
  expect(describe(nodes, 'Чекаю «так» на verify-nudge', true).isMismatch).toBe(true)
  expect(describe(nodes, 'T7: аудит', true).isMismatch).toBe(false)
  expect(describe(nodes, null, false).dsh).toBe('DSH насправді: вікно work:3 не прочитано')
})

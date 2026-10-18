import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { Lines } from '../types'
import { describe, parseDshTodo, parseTree } from './parse'

// Проба 2026-10-18 (рілс DepZsvdptkj, рішення «Так, робимо»): лише читає — grep по trees/ і
// tmux capture-pane вікна DSH; моделей не викликає.
const PROJECT = '/data/data/com.termux/files/home/AgentReachProject'
const lines = atom({ plugin: 'agents-status', key: 'lines' } as const, null)

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const refresh = async () => {
      const tree = await $.process.run(
        ['grep', '-rh', '--include=*.md', '-E', '^\\s*- \\[>\\] ', `${PROJECT}/trees`],
        { timeoutMs: 10_000 },
      ).catch(() => null)
      const tmux = await $.process.run(['tmux', 'capture-pane', '-p', '-t', 'work:3'], { timeoutMs: 10_000 })
        .catch(() => null)
      const tmuxOk = tmux !== null && tmux.exitCode === 0
      const value: Lines = describe(parseTree(tree?.stdout ?? ''), tmuxOk ? parseDshTodo(tmux.stdout) : null, tmuxOk)
      await update($, lines, () => value)
    }
    await refresh()
    $.clock.every(60_000, refresh)
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const l = await read($, lines)
    if (e.props.hasSurvey || l === null) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Text dimColor>{l.tree}</Text>
        <Text dimColor={!l.isMismatch} color={l.isMismatch ? 'yellow' : undefined}>
          {l.isMismatch ? '⚠ ' : ''}{l.dsh}
        </Text>
      </Box>
    )
  })
}

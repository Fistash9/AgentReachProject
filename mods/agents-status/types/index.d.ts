export type Lines = { tree: string; dsh: string; isMismatch: boolean }

declare module 'claude-code' {
  interface PluginState {
    'agents-status': { lines: Lines | null }
  }
}

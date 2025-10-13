import { writable } from 'svelte/store';

export type LogEntry = { ts: number; level: 'info' | 'warn' | 'error'; message: string };

export const logs = writable<LogEntry[]>([]);

export function log(level: 'info' | 'warn' | 'error', message: string) {
  const entry: LogEntry = { ts: Date.now(), level, message };
  logs.update((arr) => [entry, ...arr].slice(0, 200));
  const tag = level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log';
  // eslint-disable-next-line no-console
  console[tag](`[LOG] ${message}`);
}



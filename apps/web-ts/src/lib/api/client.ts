import createClient from 'openapi-fetch'
import type { components, paths } from './schema'

export type Bulb = components['schemas']['BulbOut']

const api = createClient<paths>({ baseUrl: '' })

/** Turns an API error body into a message the user can read. */
function unwrap<T>(result: { data?: T; error?: unknown }): T {
  if (result.data !== undefined) return result.data
  const detail = (result.error as { detail?: unknown } | undefined)?.detail
  throw new Error(typeof detail === 'string' ? detail : 'La petición falló')
}

const byId = (id: string) => ({ params: { path: { bulb_id: id } } })

export const bulbs = {
  list: async () => unwrap(await api.GET('/api/bulbs')),
  discover: async () => unwrap(await api.POST('/api/bulbs/discover')),
  turnOn: async (id: string) => unwrap(await api.POST('/api/bulbs/{bulb_id}/on', byId(id))),
  turnOff: async (id: string) => unwrap(await api.POST('/api/bulbs/{bulb_id}/off', byId(id))),
  brighten: async (id: string) => unwrap(await api.POST('/api/bulbs/{bulb_id}/brighten', byId(id))),
  dim: async (id: string) => unwrap(await api.POST('/api/bulbs/{bulb_id}/dim', byId(id))),
  setBrightness: async (id: string, level: number) =>
    unwrap(await api.PUT('/api/bulbs/{bulb_id}/brightness', { ...byId(id), body: { level } })),
  setWhite: async (id: string, kelvin: number) =>
    unwrap(await api.PUT('/api/bulbs/{bulb_id}/white', { ...byId(id), body: { kelvin } })),
  setColor: async (id: string, r: number, g: number, b: number) =>
    unwrap(await api.PUT('/api/bulbs/{bulb_id}/color', { ...byId(id), body: { r, g, b } })),
}

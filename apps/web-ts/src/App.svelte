<script lang="ts">
  import { onMount } from 'svelte'
  import { RefreshCw } from '@lucide/svelte'
  import { ModeWatcher } from 'mode-watcher'
  import { bulbs as api, type Bulb } from '$lib/api/client'
  import BulbCard from '$lib/components/BulbCard.svelte'
  import ThemeToggle from '$lib/components/ThemeToggle.svelte'
  import { Button } from '$lib/components/ui/button'

  const POLL_MS = 3000

  let bulbs = $state<Bulb[]>([])
  let loading = $state(true)
  let discovering = $state(false)
  let error = $state<string | null>(null)

  async function refresh() {
    try {
      bulbs = await api.list()
      error = null
    } catch (e) {
      error = e instanceof Error ? e.message : String(e)
    } finally {
      loading = false
    }
  }

  async function discover() {
    discovering = true
    try {
      bulbs = await api.discover()
    } catch (e) {
      error = e instanceof Error ? e.message : String(e)
    } finally {
      discovering = false
    }
  }

  async function act(change: () => Promise<Bulb>) {
    try {
      const updated = await change()
      bulbs = bulbs.map((b) => (b.id === updated.id ? updated : b))
      error = null
    } catch (e) {
      error = e instanceof Error ? e.message : String(e)
    }
  }

  // Polling: the bulbs can change outside this app (wall switch, WiZ phone app). See ADR 0001.
  onMount(() => {
    refresh()
    const timer = setInterval(refresh, POLL_MS)
    return () => clearInterval(timer)
  })
</script>

<!-- Starts from the system theme; the toggle choice is remembered in localStorage. -->
<ModeWatcher />

<main class="mx-auto max-w-5xl space-y-6 p-4 sm:p-8">
  <header class="flex items-center justify-between gap-4">
    <div>
      <h1 class="text-2xl font-semibold tracking-tight">Bombillos WiZ</h1>
      <p class="text-muted-foreground text-sm">
        {bulbs.length} encontrados en la red local
      </p>
    </div>
    <div class="flex items-center gap-2">
      <Button variant="outline" onclick={discover} disabled={discovering}>
        <RefreshCw class={discovering ? 'animate-spin' : ''} />
        {discovering ? 'Buscando…' : 'Buscar bombillos'}
      </Button>
      <ThemeToggle />
    </div>
  </header>

  {#if error}
    <p class="border-destructive/40 bg-destructive/10 text-destructive rounded-md border px-4 py-3 text-sm">
      {error}
    </p>
  {/if}

  {#if loading}
    <p class="text-muted-foreground">Cargando…</p>
  {:else if bulbs.length === 0}
    <p class="text-muted-foreground">No hay bombillos. Revisa que estén encendidos y pulsa «Buscar bombillos».</p>
  {:else}
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {#each bulbs as bulb (bulb.id)}
        <BulbCard {bulb} {act} {api} />
      {/each}
    </div>
  {/if}
</main>

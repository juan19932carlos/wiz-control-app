<script lang="ts">
  import { Minus, Plus } from '@lucide/svelte'
  import type { Bulb } from '$lib/api/client'
  import { Badge } from '$lib/components/ui/badge'
  import { Button } from '$lib/components/ui/button'
  import * as Card from '$lib/components/ui/card'
  import { Slider } from '$lib/components/ui/slider'
  import { Switch } from '$lib/components/ui/switch'

  type Props = {
    bulb: Bulb
    /** Runs one change against the server and puts the returned bulb in place. */
    act: (change: () => Promise<Bulb>) => Promise<void>
    api: typeof import('$lib/api/client').bulbs
  }
  let { bulb, act, api }: Props = $props()

  const caps = $derived(bulb.capabilities)
  const light = $derived(bulb.state)
  const disabled = $derived(!bulb.reachable)

  // While the user drags a slider, polling must not move it back.
  let brightnessDraft = $state<number | null>(null)
  let kelvinDraft = $state<number | null>(null)

  const toHex = ({ r, g, b }: { r: number; g: number; b: number }) => '#' + [r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('')
  const fromHex = (hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
</script>

<Card.Root class={disabled ? 'opacity-60' : ''}>
  <Card.Header>
    <Card.Title>Bombillo {bulb.ip.split('.').at(-1)}</Card.Title>
    <Card.Description>{bulb.ip} · {bulb.model}</Card.Description>
    <Card.Action class="flex items-center gap-3">
      {#if !bulb.reachable}
        <Badge variant="destructive">Sin respuesta</Badge>
      {:else if caps.rgb}
        <Badge variant="secondary">Color</Badge>
      {:else}
        <Badge variant="outline">Blanco</Badge>
      {/if}
      <Switch
        checked={light.on}
        {disabled}
        aria-label="Encender o apagar"
        onCheckedChange={(on) => act(() => (on ? api.turnOn(bulb.id) : api.turnOff(bulb.id)))}
      />
    </Card.Action>
  </Card.Header>

  <Card.Content class="space-y-6">
    <div class="space-y-3">
      <div class="flex items-center justify-between text-sm">
        <span class="text-muted-foreground">Brillo</span>
        <span class="tabular-nums">{brightnessDraft ?? light.brightness}%</span>
      </div>
      <div class="flex items-center gap-3">
        <Button size="icon" variant="outline" {disabled} aria-label="Bajar brillo" onclick={() => act(() => api.dim(bulb.id))}>
          <Minus />
        </Button>
        <Slider
          type="single"
          min={caps.min_brightness}
          max={100}
          step={1}
          {disabled}
          value={brightnessDraft ?? light.brightness}
          onValueChange={(v) => (brightnessDraft = v)}
          onValueCommit={async (v) => {
            await act(() => api.setBrightness(bulb.id, v))
            brightnessDraft = null
          }}
        />
        <Button size="icon" variant="outline" {disabled} aria-label="Subir brillo" onclick={() => act(() => api.brighten(bulb.id))}>
          <Plus />
        </Button>
      </div>
    </div>

    {#if caps.min_kelvin != null && caps.max_kelvin != null}
      {@const kelvin = kelvinDraft ?? light.kelvin ?? caps.min_kelvin}
      <div class="space-y-3">
        <div class="flex items-center justify-between text-sm">
          <span class="text-muted-foreground">Blanco</span>
          <span class="tabular-nums">{light.rgb && kelvinDraft == null ? '—' : `${kelvin} K`}</span>
        </div>
        <div class="kelvin-track rounded-full p-1">
          <Slider
            type="single"
            min={caps.min_kelvin}
            max={caps.max_kelvin}
            step={100}
            {disabled}
            value={kelvin}
            onValueChange={(v) => (kelvinDraft = v)}
            onValueCommit={async (v) => {
              await act(() => api.setWhite(bulb.id, v))
              kelvinDraft = null
            }}
          />
        </div>
        <div class="text-muted-foreground flex justify-between text-xs">
          <span>Cálido</span><span>Frío</span>
        </div>
      </div>
    {/if}

    {#if caps.rgb}
      <label class="flex items-center justify-between text-sm">
        <span class="text-muted-foreground">Color</span>
        <input
          type="color"
          class="h-9 w-16 cursor-pointer rounded-md border bg-transparent"
          {disabled}
          value={toHex(light.rgb ?? { r: 255, g: 255, b: 255 })}
          onchange={(e) => {
            const [r, g, b] = fromHex(e.currentTarget.value)
            act(() => api.setColor(bulb.id, r, g, b))
          }}
        />
      </label>
    {/if}
  </Card.Content>
</Card.Root>

<style>
  .kelvin-track {
    background: linear-gradient(to right, #ffb46b, #fff4e5, #d6e4ff);
  }
</style>

<script lang="ts">
  import { Moon, Sun } from '@lucide/svelte'
  import { mode, toggleMode } from 'mode-watcher'
  import { Button } from '$lib/components/ui/button'

  const label = $derived(mode.current === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro')
</script>

<Button variant="outline" size="icon" onclick={toggleMode} aria-label={label} title={label}>
  <Sun class="scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
  <Moon class="absolute scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
</Button>

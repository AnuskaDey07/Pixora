<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useImagesStore } from '@/stores/images'
import { useEditorStore, type EditorTool } from '@/stores/editor'

const route = useRoute()
const images = useImagesStore()
const editor = useEditorStore()

const tools: { id: EditorTool; label: string; group: string }[] = [
  { id: 'resize',         label: 'Resize',           group: 'Basic' },
  { id: 'convert',        label: 'Convert format',   group: 'Basic' },
  { id: 'remove_bg',      label: 'Remove background', group: 'Edit' },
  { id: 'inpaint',        label: 'Inpaint / erase',  group: 'Edit' },
  { id: 'img2img',        label: 'Image to image',   group: 'Generate' },
  { id: 'generate',       label: 'Text to image',    group: 'Generate' },
  { id: 'controlnet',     label: 'Sketch guided',    group: 'Generate' },
  { id: 'detect_nsfw',    label: 'Detect NSFW',      group: 'Detect' },
  { id: 'detect_ai',      label: 'Detect AI',        group: 'Detect' },
  { id: 'detect_objects', label: 'Detect objects',   group: 'Detect' },
  { id: 'embed',          label: 'Embed (CLIP)',     group: 'Search' },
]

const showResult = ref(false)

const currentImage = computed(() =>
  editor.imageId ? images.items.find((i) => i.id === editor.imageId) : null,
)

const hasImage = computed(() => !!editor.imageId)

onMounted(async () => {
  if (images.items.length === 0) await images.refresh()
  const qid = route.query.image as string | undefined
  if (qid) editor.setImage(qid)
  else if (images.items[0]) editor.setImage(images.items[0].id)
})

async function run() {
  showResult.value = false
  await editor.run()
  showResult.value = true
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-6 py-8">
    <h1 class="text-2xl font-bold">Editor</h1>
    <p class="mt-1 text-sm text-slate-400">Pick a tool, adjust params, run.</p>

    <div class="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
      <!-- Sidebar -->
      <aside class="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
        <h2 class="mb-3 text-xs uppercase tracking-wide text-slate-500">Tool</h2>
        <div class="space-y-3">
          <div v-for="group in ['Basic','Edit','Generate','Detect','Search']" :key="group">
            <div class="mb-1 text-xs text-slate-500">{{ group }}</div>
            <button
              v-for="t in tools.filter(x => x.group === group)"
              :key="t.id"
              @click="editor.setTool(t.id)"
              class="block w-full rounded-md px-3 py-1.5 text-left text-sm transition"
              :class="editor.tool === t.id
                ? 'bg-brand-600 text-white'
                : 'text-slate-300 hover:bg-slate-800'"
            >{{ t.label }}</button>
          </div>
        </div>

        <div class="mt-6">
          <label class="mb-1 block text-xs uppercase tracking-wide text-slate-500">Source image</label>
          <select
            :value="editor.imageId ?? ''"
            @change="(e) => editor.setImage((e.target as HTMLSelectElement).value || null)"
            class="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm"
          >
            <option value="">— none —</option>
            <option v-for="img in images.items" :key="img.id" :value="img.id">
              {{ img.filename ?? img.id.slice(0, 8) }}
            </option>
          </select>
        </div>
      </aside>

      <!-- Main -->
      <section class="space-y-4">
        <div class="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
          <h2 class="mb-3 text-xs uppercase tracking-wide text-slate-500">Params</h2>

          <div class="grid grid-cols-2 gap-3">
            <!-- Resize -->
            <template v-if="editor.tool === 'resize'">
              <label class="text-sm">
                <span class="text-slate-400">Width</span>
                <input type="number" v-model.number="editor.params.width as number"
                  class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5" />
              </label>
              <label class="text-sm">
                <span class="text-slate-400">Height</span>
                <input type="number" v-model.number="editor.params.height as number"
                  class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5" />
              </label>
            </template>

            <!-- Convert -->
            <template v-else-if="editor.tool === 'convert'">
              <label class="text-sm col-span-2">
                <span class="text-slate-400">Format</span>
                <select v-model="editor.params.format as string"
                  class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5">
                  <option>PNG</option><option>JPEG</option><option>WEBP</option>
                </select>
              </label>
            </template>

            <!-- Generate / Img2Img / Inpaint / Controlnet -->
            <template v-else-if="['generate','img2img','inpaint','controlnet'].includes(editor.tool)">
              <label class="text-sm col-span-2">
                <span class="text-slate-400">Prompt</span>
                <textarea v-model="editor.params.prompt as string" rows="2"
                  class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5"></textarea>
              </label>
              <template v-if="editor.tool === 'generate'">
                <label class="text-sm">
                  <span class="text-slate-400">Width</span>
                  <input type="number" v-model.number="editor.params.width as number"
                    class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5" />
                </label>
                <label class="text-sm">
                  <span class="text-slate-400">Height</span>
                  <input type="number" v-model.number="editor.params.height as number"
                    class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5" />
                </label>
              </template>
              <template v-if="editor.tool === 'img2img'">
                <label class="text-sm">
                  <span class="text-slate-400">Strength (0–1)</span>
                  <input type="number" step="0.05" min="0" max="1" v-model.number="editor.params.strength as number"
                    class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5" />
                </label>
              </template>
              <template v-if="editor.tool === 'controlnet'">
                <label class="text-sm">
                  <span class="text-slate-400">Control strength</span>
                  <input type="number" step="0.1" v-model.number="editor.params.control_strength as number"
                    class="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5" />
                </label>
              </template>
            </template>

            <!-- Detection / Embed -->
            <template v-else>
              <p class="col-span-2 text-sm text-slate-500">No params required.</p>
            </template>
          </div>

          <div class="mt-4 flex items-center gap-3">
            <button
              @click="run"
              :disabled="editor.busy || (!hasImage && editor.tool !== 'generate')"
              class="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
            >{{ editor.busy ? 'Running…' : 'Run' }}</button>
            <span v-if="editor.isRunning" class="text-xs text-slate-400">
              job {{ editor.job?.status }}…
            </span>
          </div>
        </div>

        <!-- Preview -->
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 class="mb-2 text-xs uppercase tracking-wide text-slate-500">Source</h3>
            <div class="flex aspect-video items-center justify-center overflow-hidden rounded-md bg-slate-950">
              <img v-if="currentImage?.thumb_url" :src="currentImage.thumb_url" class="max-h-full max-w-full object-contain" />
              <p v-else class="text-sm text-slate-600">no image</p>
            </div>
          </div>

          <div class="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <h3 class="mb-2 text-xs uppercase tracking-wide text-slate-500">Result</h3>
            <div class="flex aspect-video items-center justify-center overflow-hidden rounded-md bg-slate-950">
              <img v-if="editor.resultUrl" :src="editor.resultUrl" class="max-h-full max-w-full object-contain" />
              <pre v-else-if="editor.resultMeta" class="max-h-full overflow-auto p-2 text-xs text-slate-300">{{ JSON.stringify(editor.resultMeta, null, 2) }}</pre>
              <p v-else class="text-sm text-slate-600">run a tool to see output</p>
            </div>
          </div>
        </div>

        <div v-if="editor.error" class="rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {{ editor.error }}
        </div>
      </section>
    </div>
  </div>
</template>

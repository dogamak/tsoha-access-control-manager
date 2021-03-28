<template>
  <div class="rounded-xl bg-white shadow-lg overflow-hidden">
    <div class="bg-gradient-to-r from-blue-400 to-blue-500 w-full h-11 font-bold items-center flex px-4 text-blue-50">
      <div>
        <slot name="header-left">
          {{ header }}
        </slot>
      </div>
      <div class="flex-grow"></div>
      <div>
        <slot name="header-right"></slot>
      </div>
    </div>
    <div :class="noPadding ? '' : 'p-3'">
        <slot></slot>
        <div class="clear-both"></div>
    </div>
    <div v-if="$slots.footer" class="bg-gradient-to-r from-gray-100 to-gray-200 py-2 w-full font-bold items-center flex px-4 text-blue-50" style="min-height: 3rem">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
    export default {
        props: {
            header: String,
            noPadding: Boolean,
        },
    };
</script>
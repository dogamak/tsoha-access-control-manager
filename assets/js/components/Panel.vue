<template>
  <div class="rounded-xl bg-white shadow-lg overflow-hidden">
    <div class="bg-gradient-to-r from-blue-400 to-blue-500 w-full h-11 font-bold items-center flex px-4 text-blue-50">
      {{ header }}
    </div>
    <div class="pt-2 pb-5 px-5">
        <slot></slot>
    </div>
  </div>
</template>

<script>
    export default {
        props: {
            header: String,
        },
    };
</script>

<style>
    div {
        @apply bg-red-600;
    }
</style>
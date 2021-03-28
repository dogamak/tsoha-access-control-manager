<template>
    <div
        style="position: absolute; display: flex; align-items: center; vertical-align: center; inset: 0; z-index: 1000"
        class="dialog-backdrop"
    >
        <div @click="$emit('close')" class="inset-0 absolute bg-opacity-10 bg-black"></div>
        <div class="rounded-xl z-10 mx-auto bg-white shadow-2xl overflow-hidden" style="min-width: 20rem">
            <div class="bg-gradient-to-r from-blue-400 to-blue-500 w-full h-11 font-bold items-center flex px-4 text-blue-50 dialog-header">
                <div>{{ header }}</div>
                <div class="flex-grow"></div>
                <div>
                    <button
                        class="border-2 px-2 rounded-sm border-blue-200 hover:border-white hover:text-white"
                        @click="$emit('close')"
                    >
                        Close
                    </button>
                </div>
            </div>
            <div class="pt-3 px-5 pb-2 dialog-content overflow-y-auto max-h-96">
                <slot></slot>
            </div>
        </div>
  </div>
</template>

<script>
  export default {
      props: ['header'],
      emits: ['close'],
  };
</script>

<style lang="scss">
    .dialog-backdrop {
        position: absolute;
        inset: 0;
        background-color: rgba(0,0,0,0.2);
    }
</style>
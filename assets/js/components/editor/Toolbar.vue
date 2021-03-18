<template>
  <div class="m-10 bg-white w-14 transition-all rounded-2xl shadow-xl p-2 toolbar flex flex-col gap-2 relative">
    <div v-for="(tool, i) in tools" class="flex items-center overflow-hidden cursor-pointer tool" @click="onSelect(tool, i)" :class="{ selected: selected === i }">
      <span
        class="inline-block h-10 w-10 flex-shrink-0 rounded-xl text-white font-extrabold flex items-center justify-center text-xl icon"
        :class="[ selected === i ? 'bg-blue-400' : 'bg-gray-200' ]"
      >
        {{ tool.icon }}
      </span>
      <span class="inline-block pl-3 pr-2 tool-label hidden whitespace-nowrap">{{ tool.label }}</span>
    </div>
    <span class="absolute top-0 right-0">
      <span style="transform: rotate(90deg) translate(0%, -100%); transform-origin: 0% 0%; position: absolute; top: 1em; left: 1.5em text-shadow: 0px 0px rgba(0,0,0,1)" class="font-bold text-gray-400">Toolbar</span>
    </span>
  </div>
</template>

<script>
  export default {
    props: {
      tools: Array,
      value: Object,
    },

    data () {
      return {
        selected: null,
      };
    },

    watch: {
      value () {
        this.selected = this.tools.findIndex(t => t === this.value);

        if (this.selected === -1) {
          this.selected = null;
        }
      },
    },

    methods: {
      onSelect (tool, i) {
        this.$emit('input', tool);
      },
    },
  };
</script>

<style>
  .toolbar:hover {
    width: 10em;
  }

  .tool-label {
    display: inline-block;
  }

  .tool:not(.selected):hover .icon {
    background-color: #bfdbfe;
  }
  
</style>

<template>
  <div class="rounded-xl mx-auto w-80 bg-white shadow-lg overflow-hidden dialog">
    <div class="bg-gradient-to-r from-blue-400 to-blue-500 w-full h-11 font-bold items-center flex px-4 text-blue-50 dialog-header">
      Room Options
    </div>
    <div class="pt-3 px-5 pb-2 dialog-content">
      <input type="text" class="block border-2 rounded-md py-1 px-2 w-full" placeholder="Room name" v-model="name" />
      <input type="submit" value="Create room" class="bg-gradient-to-r from-blue-400 to-blue-500 px-3 py-1 rounded-lg text-blue-50 mt-4" @click="createRoom"/>
    </div>
  </div>
</template>

<script>
  export default {
    data () {
      return {
        name: '',
      };
    },

    methods: {
      createRoom () {
        this.$close({
          name: this.name,
        });
      },
    },
  };
</script>

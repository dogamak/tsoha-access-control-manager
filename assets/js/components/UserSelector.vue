<template>
    <div class="mr-6 relative">
        <div
            :class="['bg-gray-100 h-9 relative z-10 py-1 flex px-3 text-gray-900 border-2 border-gray-100 items-center outline-none focus:border-blue-400 mt-1 rounded-sm', { 'cursor-pointer': all_users.length > 0 }]"
            @click="toggle"
        >
            <span v-if="displayValue">{{ displayValue }}</span>
            <span class="text-sm text-gray-500" v-if="all_users.length === 0">No selectable users</span>
            <div class="flex-grow"></div>
            <div
                v-if="all_users.length > 0"
                class="arrow w-0 h-0 transition-all"
                :style="{
                    border: '0.5rem solid transparent',
                    borderTopColor: 'gray',
                    transformOrigin: '50% 33%',
                    transform: drawerVisible ? 'rotate(180deg)' : 'translate(0, 0.25rem)',
                }"
            ></div>
        </div>

        <div v-show="drawerVisible" class="absolute w-full shadow-md z-50">
            <div
                v-for="user in all_users"
                :key="user.id"
                class="py-2 px-3 bg-gray-50 border-l-2 border-gray-50 hover:border-gray-100 hover:bg-gray-100 cursor-pointer"
                @click="select(user)"
            >
                <span>{{ user.name || user.username }}</span>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        props: ['modelValue'],

        inject: ['all_users'],

        data () {
            return {
                drawerVisible: false,
            };
        },

        methods: {
            toggle () {
                this.drawerVisible ^= true;
            },

            select (user) {
                this.drawerVisible = false;
                this.$emit('update:modelValue', user);
            },
        },

        computed: {
            displayValue () {
                if (this.modelValue) {
                    if (this.modelValue.name) {
                        return this.modelValue.name;
                    } else if (this.modelValue.username) {
                        return this.modelValue.username;
                    }
                } else {
                    return null;
                }
            },
        },
    };
</script>
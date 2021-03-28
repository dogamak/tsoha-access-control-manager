<template>
    <div>
        <div class="w-full h-14 bg-gradient-to-r from-blue-400 to-blue-500 shadow-md flex items-center px-5 text-white">
            <span class="font-bold text-xl">Access Control Manager</span>

            <template v-for="segment in breadcrumb" :key="segment">
                <div class="breadcrumb-separator"></div>
                <a v-if="segment.url" :href="segment.url" class="text-xl" :key="segment + '-if'">{{ segment.label }}</a>
                <span v-else class="text-xl" :key="segment + '-else'">{{ segment.label }}</span>
            </template>

            <template v-if="$user">
                <span class="flex-grow"></span>
                <span class="mr-3">{{ $user.username }}</span>
                <a
                    :href="$url_for('logout')"
                    class="bg-white text-blue-500 px-3 py-1 rounded-2xl font-bold"
                >
                    Log out
                </a>
            </template>
        </div>
        <div>
            <slot></slot>
        </div>
    </div>
</template>

<script>
    export default {
        props: ['breadcrumb'],
    };
</script>

<style>
    .breadcrumb-separator {
        width: 10px;
        height: 10px;
        border-width: 2px;
        border-style: solid;
        @apply border-blue-300;
        border-left-color: transparent;
        border-bottom-color: transparent;
        transform: translate(0px, 33%) rotate(45deg);
        margin-left: 5px;
        margin-right: 10px;
    }
</style>
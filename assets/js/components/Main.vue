<template>
    <div>
        <div class="w-full h-14 bg-gradient-to-r from-blue-400 to-blue-500 shadow-md flex items-center px-5 text-white">
            <span class="font-bold text-xl">Access Control Manager</span>

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
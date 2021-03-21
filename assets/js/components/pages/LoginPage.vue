<template>
    <div class="p-20">
        <div
            v-if="error"
            class="mt-10 rounded-xl mx-auto w-80 bg-white shadow-lg overflow-hidden mb-10"
        >
            <div class="bg-gradient-to-r from-red-400 to-red-500 w-full h-11 font-bold items-center flex px-4 text-blue-50">
                Error
            </div>
            <div class="pt-3 px-5">
                <div class="mb-4 text-gray-600">
                    {{ error }}
                </div>
            </div>
        </div>

        <div class="rounded-xl mx-auto w-80 bg-white shadow-lg overflow-hidden">
            <div class="bg-gradient-to-r from-blue-400 to-blue-500 w-full h-11 font-bold items-center flex px-4 text-blue-50">
                Authenticate
            </div>
            <div class="pt-3 px-5 pb-2">
                <div class="mb-4 text-gray-600">
                    Authentication is required to access this page.
                </div>
                <div class="w-full border-b-2 border-gray-200 mb-4"></div>
                <form action="/login" method="POST">
                    <div class="mb-4">
                        <input type="text" name="username" class="border-2 rounded-md py-1 px-2 w-full" placeholder="Username" :value="username" />
                    </div>
                    <div>
                        <input type="password" name="password" class="border-2 rounded-md py-1 px-2 w-full" placeholder="Password" />
                    </div>
                    <input type="submit" value="Login" class="bg-gradient-to-r from-blue-400 to-blue-500 px-3 py-1 rounded-lg text-blue-50 mt-4" />
                </form>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        props: ['error', 'username'],
    };
</script>
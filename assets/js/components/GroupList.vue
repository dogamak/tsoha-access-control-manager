<template>
    <table class="group-list-table w-full">
        <tr
            v-for="group in groups"
            :key="group.id"
            class="group cursor-pointer"
            @click="$emit('click', group)"
        >
            <td class="p-2 group-hover:bg-gray-100 rounded-l-full">
                <div class="rounded-full w-8 h-8 bg-gray-300"></div>
            </td>
            <td class="pl-2 pr-8 whitespace-nowrap py-2 group-hover:bg-gray-100">
                <span class="text-sm text-gray-800">{{ group.name }}</span>
            </td>
            <td class="p-2 group-hover:bg-gray-100 whitespace-nowrap text-right">
                <span v-if="group.subgroups" class="text-sm text-gray-500">{{ group.subgroups.length }} sub-groups</span>
            </td>
            <td class="p-2 pr-4 group-hover:bg-gray-100 whitespace-nowrap rounded-r-full text-right">
                <span v-if="group.members" class="text-sm text-gray-500">{{ group.members.length }} members</span>
            </td>
        </tr>
    </table>
</template>

<script>
    export default {
        props: ['groups'],

        emits: ['click'],
    };
</script>
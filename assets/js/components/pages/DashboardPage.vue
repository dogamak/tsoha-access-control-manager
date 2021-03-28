<template>
    <div class="lg:flex gap-10 p-10 justify-around items-start">
        <Panel header="Rooms" class="mb-10 xl:w-96 md:flex-grow xl:flex-grow-0">
        </Panel>
        <Panel header="Groups" class="mb-10 xl:w-96 md:flex-grow xl:flex-grow-0">
            <div class="p-3">
                <GroupList :groups="all_groups" @click="$navigate('group_details', { id: $event.id })" />
            </div>
        </Panel>
        <Panel header="People" class="mb-10 xl:w-96 md:flex-grow xl:flex-grow-0">
            <div class="p-3">
                <li
                    v-for="user in all_users"
                    :key="user.id"
                    class="flex gap-3 items-center my-2 p-2 cursor-pointer rounded-full hover:bg-gray-100"
                    @click="$navigate('user_details', { username: user.username })"
                >
                    <div
                        class="rounded-full w-8 h-8 bg-gray-300 bg-cover bg-center"
                        :style="user.avatar ? `background-image: url('${user.avatar.url}')` : ''"
                    ></div>
                    <span class="text-sm text-gray-800">
                        {{ user.username }}
                    </span>
                </li>
            </div>
        </Panel>
    </div>
</template>

<script>
    import Panel from '../Panel.vue';
    import GroupList from '../GroupList.vue';

    export default {
        components: { GroupList, Panel },

        inject: ['all_users', 'all_groups'],

        props: [ 'groups' ],
    };
</script>
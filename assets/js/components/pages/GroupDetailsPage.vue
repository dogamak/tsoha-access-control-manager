<template>
    <div class="p-10 flex gap-10 items-start">
        <Panel header="Groups">
            <GroupList :groups="groups" />
        </Panel>
        <Panel :header="'Group: ' + group.name" class="w-80">
            <template v-if="group.parent">
                <h3 class="font-semibold my-3 text-gray-700" v-if="group.parent">
                    <span>Parent group</span>
                </h3>

                <div
                    class="flex cursor-pointer gap-3 items-center my-2 p-2 rounded-full hover:bg-gray-100"
                    @click="$navigate('group_details', { id: group.parent.id })"
                >
                    <div class="rounded-full w-8 h-8 bg-gray-300"></div>
                    <span class="text-sm text-gray-800">
                        {{ group.parent.name }}
                    </span>
                </div>
            </template>

            <h3 class="font-semibold text-gray-700 my-3 flex items-center">
                <span>Subgroups</span>
                <span class="flex-grow"></span>
                <span
                    v-if="membership && membership.manage_users"
                    class="text-xl font-bold text-blue-500 rounded-full hover:bg-blue-400 cursor-pointer hover:text-white inline-block h-5 w-5 text-center"
                    style="line-height: 0.9em"
                >+</span>
            </h3>

            <ul v-if="group.subgroups.length > 0">
                <li
                    v-for="subgroup in group.subgroups"
                    :key="subgroup.id"
                    class="flex cursor-pointer gap-3 items-center my-2 p-2 rounded-full hover:bg-gray-100"
                    @click="$navigate('group_details', { id: subgroup.id })"
                >
                    <div class="rounded-full w-8 h-8 bg-gray-300"></div>
                    <span class="text-sm text-gray-800">
                        {{ subgroup.name }}
                    </span>
                </li>
            </ul>
            <span v-else class="text-sm text-gray-500">No subgroups</span>

            <h3 class="font-semibold text-gray-700 my-3 flex items-center">
                <span>Members</span>
                <span class="flex-grow"></span>
                <span
                    v-if="membership && membership.create_users"
                    class="text-xl font-bold text-blue-500 rounded-full hover:bg-blue-400 cursor-pointer hover:text-white inline-block h-5 w-5 text-center"
                    style="line-height: 0.9em"
                >+</span>
            </h3>
            <ul v-if="group.members.length > 0">
                <li
                    v-for="member in group.members"
                    :key="member.id"
                    class="flex gap-3 items-center my-2 p-2 rounded-full hover:bg-gray-100"
                >
                    <div class="rounded-full w-8 h-8 bg-gray-300"></div>
                    <span class="text-sm text-gray-800">
                        {{ member.username }}
                    </span>
                </li>
            </ul>
            <span v-else class="text-sm text-gray-500">No members</span>
        </Panel>
    </div>
</template>

<script>
    import Panel from '../Panel.vue';
    import GroupList from '../GroupList.vue';

    export default {
        components: { Panel, GroupList },

        props: ['group', 'membership', 'groups'],
    };
</script>

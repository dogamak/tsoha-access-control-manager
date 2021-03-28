<template>
    <div class="p-10">
        <Panel header="Groups" class="inline-block">
            <GroupList :groups="all_groups" @click="$navigate('group_details', { id: $event.id })" />
        </Panel>
    </div>
</template>

<script>
    import Panel from '../Panel.vue';
    import GroupList from '../GroupList.vue';

    export default {
        components: { Panel, GroupList },

        inject: ['all_groups'],

        props: ['groups'],
    };
</script>

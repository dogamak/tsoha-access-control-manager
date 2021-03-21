<template>
    <div class="p-10">
        <Panel header="Groups" class="inline-block">
            <GroupList :groups="groups" />
        </Panel>
    </div>
</template>

<script>
    import Panel from '../Panel.vue';
    import GroupList from '../GroupList.vue';

    export default {
        components: { Panel, GroupList },

        props: ['groups'],
    };
</script>

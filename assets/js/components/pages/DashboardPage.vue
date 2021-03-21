<template>
    <div class="lg:flex gap-10 p-10 justify-around items-start">
        <Panel header="Rooms" class="mb-10 xl:w-96 md:flex-grow xl:flex-grow-0">
        </Panel>
        <Panel header="Groups" class="mb-10 xl:w-96 md:flex-grow xl:flex-grow-0">
            <GroupList :groups="groups" />
        </Panel>
        <Panel header="People" class="mb-10 xl:w-96 md:flex-grow xl:flex-grow-0">
        </Panel>
    </div>
</template>

<script>
    import Panel from '../Panel.vue';
    import GroupList from '../GroupList.vue';

    export default {
        components: { GroupList, Panel },

        props: [ 'groups' ],
    };
</script>
<template>
    <div class="p-2 h-11 bg-gray-100 flex flex-wrap gap-1 items-center">
        <div
            v-for="group in modelValue"
            :key="group.id"
            class="px-2 py-1 bg-gray-200 cursor-pointer"
            @click="selectGroup(group)"
        >
            <span class="text-sm">{{ group.name }}</span>
        </div>

        <div
            class="px-2 py-1 bg-blue-500 text-white font-bold text-sm cursor-pointer"
            @click="showGroupSelectDialog = true"
            v-if="groups.length > 0"
        >
            Add +
        </div>

        <div v-if="groups.length === 0" class="ml-3 text-gray-500 text-sm">No available groups</div>

        <teleport to="body">
            <Dialog
                header="Add Group"
                v-if="showGroupSelectDialog"
                @close="showGroupSelectDialog = false"
            >
                <GroupList
                    :groups="groups"
                    @click="handleAddGroup"
                />
            </Dialog>

            <Dialog
                header="Group Details"
                v-if="selectedGroupId !== null"
                @close="selectedGroupId = null"
            >
                <div class="grid gap-3 text-sm text-gray-700" style="grid-template-columns: auto max-content">
                    <template v-for="permission in permissions" :key="permission.key">
                        <label class="whitespace-nowrap">{{ permission.label }}</label>
                        <div class="justify-self-center self-center">
                            <input
                                type="checkbox"
                                :checked="selectedGroup && selectedGroup[permission.key]"
                                @change="onPermissionChange($event, permission)" />
                        </div>
                    </template>
                </div>

                <Button label="Remove from group" dangerous class="mb-3 mt-5" @click="removeGroup" />
            </Dialog>
        </teleport>
    </div>
</template>

<script>
    import GroupList from './GroupList.vue';
    import Dialog from './Dialog.vue';
    import Button from './Button.vue';

    import { group_permissions } from '../models/user.js';

    export default {
        components: { Button, Dialog, GroupList },

        props: ['modelValue'],

        emits: ['update:modelValue'],

        inject: ['all_groups'],

        getProperties () {
            return {
                width: 2,
                height: 1,
                hideRemoveButton: true,
            };
        },

        data () {
            return {
                showGroupSelectDialog: false,
                selectedGroupId: null,
                permissions: group_permissions,
            };
        },

        methods: {
            handleAddGroup (group) {
                this.$emit('update:modelValue', [ ...this.modelValue, group ]);

                if (this.groups.length === 1) {
                    this.showGroupSelectDialog = false;
                }
            },

            selectGroup (group) {
                this.selectedGroupId = group.id;
            },

            removeGroup () {
                let copy = [ ...this.modelValue ];

                let index = copy.findIndex(({ id }) => id === this.selectedGroupId);
                copy.splice(index, 1);

                this.$emit('update:modelValue', copy);
                this.selectedGroupId = null;
            },

            onPermissionChange (evt, permission) {
                let copy = [ ...this.modelValue ];
                let index = copy.findIndex(({ id }) => id === this.selectedGroupId);

                copy[index] = {
                    ... copy[index],
                    [permission.key]: evt.target.checked,
                };

                this.$emit('update:modelValue', copy);
            },
        },

        computed: {
            groups () {
                return this.all_groups
                    .filter(({ id }) => this.modelValue.findIndex((el) => el.id === id) === -1);
            },

            selectedGroup () {
                if (this.selectedGroupId === null)
                    return null;

                return this.modelValue.find(({ id }) => id === this.selectedGroupId);
            },
        },
    }
</script>

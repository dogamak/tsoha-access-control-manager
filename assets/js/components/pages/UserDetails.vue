<template>
    <div class="p-10 flex flex-col m-auto justify-items-stretch gap-10" style="width: 50rem">
        <Panel header="Account Details">
            <template v-slot:header-right>
                <button
                    v-if="!editing"
                    class="border-2 px-2 rounded-sm border-blue-200 hover:border-white hover:text-white"
                    @click="editing = true"
                >
                    Edit
                </button>
                <button
                    v-if="editing && addableFields"
                    class="border-2 mr-3 px-2 rounded-sm border-blue-200 hover:border-white hover:text-white"
                    @click="$refs.prop_view.showPropertyDialog()"
                >
                    Add Field
                </button>
                <button
                    v-if="editing"
                    class="border-2 border-blue-300 hover:border-white px-2 rounded-sm text-white font-bold bg-blue-400"
                    @click="save"
                >
                    Save
                </button>
            </template>
            <template v-slot:default>
                <div class="py-5 px-5">
                    <PropertyView
                        ref="prop_view"
                        :model="userModel"
                        :modelValue="modifiedUser"
                        :editing="editing"
                        @additionalPropertiesAvailable="addableFields = $event.length > 0"
                        @propertyChange="onPropertyChange" />

                    <div class="clear-both"></div>
                </div>
            </template>
        </Panel>
        <Panel header="Groups">
            <GroupList :groups="groups_" @click="$navigate('group_details', { id: $event.id })" />
        </Panel>
        <Panel header="Has Access To">
        </Panel>

        <teleport to="body">
            <Dialog header="Add Field" v-if="displayFieldSelectDialog" @close="displayFieldSelectDialog = false">
                <div>
                    <div
                        v-for="field in missing_fields"
                        :key="field.label"
                        @click="addField(field)"
                    >
                        <span>{{ field.label }}</span>
                    </div>
                </div>
            </Dialog>
        </teleport>
    </div>
</template>

<script>
    import { h } from 'vue';
    import { url_for } from '../../flask.js';

    import Panel from '../Panel.vue';
    import GroupList from '../GroupList.vue';
    import PropertyView from '../PropertyView.vue';
    import Dialog from '../Dialog.vue';
    import UserLink from '../UserLink.vue';

    import { UserModel } from '../../models/user.js';

    export default {
        components: { GroupList, Panel, PropertyView, Dialog },

        props: ['user', 'groups'],

        data () {
            return {
                userModel: UserModel,
                displayFieldSelectDialog: false,
                addableFields: false,
                editing: false,
                dirtyProperties: [],
                modifiedUser: JSON.parse(JSON.stringify(this.user)),
                originalUser: JSON.parse(JSON.stringify(this.user)),
                fields: [
                    {
                        label: 'Real Name',
                        key: 'name',
                        required: true,
                    },
                    {
                        label: 'Username',
                        key: 'username',
                        required: true,
                    },
                    {
                        label: 'Email Address',
                        key: 'email',
                    },
                    {
                        label: 'Role',
                        key: 'role',
                    },
                    {
                        label: 'Supervisor',
                        key: 'supervisor',
                        component: UserLink,
                        noEdit: true,
                    },
                ],
            };
        },

        methods: {
            onPropertyChange ({ property, value }) {
                const index = this.dirtyProperties.indexOf(property.key);
                const isDirty = this.originalUser[property.key] !== value;
                const wasDirty = index !== -1;

                console.log(property, value);

                if (isDirty && !wasDirty) {
                    this.dirtyProperties = [ ...this.dirtyProperties, property.key ];
                } else if (!isDirty && wasDirty) {
                    this.dirtyProperties.splice(index, 1);
                }

                this.modifiedUser = {
                    ... this.modifiedUser,
                    [property.key]: value,
                };
            },

            save () {
                const form = document.createElement('form');

                form.method = 'POST';
                form.action = url_for('user_edit', { username: this.modifiedUser.username });

                if (this.dirtyProperties.length === 0) {
                    this.editing = false;
                    return;
                }


                for (const key of this.dirtyProperties) {
                    const el = document.createElement('input');
                    el.type = 'text';
                    el.value = this.modifiedUser[key];
                    el.name = key;

                    form.appendChild(el);
                }

                const el = document.createElement('input');
                el.type = 'text';
                el.value = this.$csrf_token;
                el.name = 'csrf_token';

                form.appendChild(el);

                document.body.appendChild(form);
                form.submit();
            },

            handleAddField () {
                this.displayFieldSelectDialog = true;
            },

            addField (field) {
                this.displayFieldSelectDialog = false;

                this.dirtyProperties.push(field);
            },
        },

        computed: {
            groups_ () {
                return this.groups.map((membership) => membership.group);
            },

            present_fields () {
                return this.fields.filter(({ key }) => this.modifiedUser[key] !== null || this.dirtyProperties.indexOf(key) !== -1);
            },

            missing_fields () {
                return this.fields.filter(({ key }) => this.modifiedUser[key] === null && this.dirtyProperties.indexOf(key) === -1);
            },
        },
    }
</script>
<template>
    <div class="flex justify-center">
        <div class="p-10 inline-flex flex-col justify-items-stretch gap-10">
            <Panel header="Create User">
                <template v-slot:default>

                    <div class="py-5 px-5">
                        <PropertyView
                            :model="userModel"
                            permissionLevel="supervisor"
                            v-model="user"
                            @additionalPropertiesAvailable="showAddPropertyButton = $event.length > 0"
                            ref="prop_view"
                            editing
                        />
                    </div>
                </template>
                <template v-slot:footer>
                    <Button class="mr-1" label="Create" primary @click="createUser" />
                    <Button
                        v-if="showAddPropertyButton"
                        @click="$refs.prop_view.showPropertyDialog()"
                        label="Add Property"
                    />
                </template>
            </Panel>
        </div>
    </div>
</template>

<script>
    import PropertyView from '../PropertyView.vue';
    import Panel from '../Panel.vue';
    import Button from '../Button.vue';

    import { UserFields, UserModel, GroupPermissions } from '../../models/user.js';

    function loadUrlAsBase64 (url) {
    }

    const field_transformers = {
        [UserFields.PHOTO]: ({ url }) => {
            if (!url || !url.startsWith('blob:'))
                return Promise.resolve(url);

            return fetch(url)
                .then((res) => res.blob())
                .then((blob) => {
                    return new Promise((resolve) => {
                        const reader = new FileReader();

                        reader.onload = () => {
                            resolve({
                                data: reader.result.replace(/^data:.+;base64,/, ''),
                                mimetype: blob.type,
                            });
                        };

                        reader.readAsDataURL(blob);
                    });
                });
        },

        [UserFields.SUPERVISOR]: ({ id }) => id,

        [UserFields.GROUPS]: (groups) => {
            const filterEntry = ([key, value]) => {
                return key === 'id' || GroupPermissions.find((perm) => perm.key === key);
            };

            return groups.map((group) => Object.fromEntries(Object.entries(group).filter(filterEntry)));
        },
    };

    export default {
        components: { Panel, PropertyView, Button },

        props: ['group'],

        provide: {
            users: [
                {
                    id: 123,
                    name: 'Test User',
                    username: 'test-user',
                    email: 'test.user@test.org',
                    supervisor: { id: 321, name: 'Supervisor' },
                },
                {
                    id: 321,
                    name: 'Another User',
                    username: 'test-user',
                    email: 'test.user@test.org',
                    supervisor: { id: 321, name: 'Supervisor' },
                }
            ],
        },

        data () {
            const user = {
                photo: '',
                groups: [ this.group ],
            };

            Object.values(UserModel)
                .filter(({ required }) => required)
                .forEach(({ key }) => user[key] = '');

            return {
                user,
                userModel: UserModel,
                showAddPropertyButton: false,
            };
        },

        methods: {
            async createUser () {
                const url = this.$url_for('create_user', { group: this.group.id });

                const entries = await Promise.all(Object.entries(this.user)
                    .map(async ([key, value]) => {
                        const [ property ] = Object.entries(UserModel)
                            .find(([_, descriptor]) => descriptor.key === key);
                        
                        const transform = field_transformers[property];

                        if (transform) {
                            const result = transform(value);

                            if (result && typeof result.then === 'function') {
                                return [key, await result];
                            } else {
                                return [key, result];
                            }
                        } else {
                            return [key, value];
                        }
                    }));

                const transformed = Object.fromEntries(entries);

                console.log(getCookie('csrf_access_token'));

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': getCookie('csrf_access_token'),

                    },
                    body: JSON.stringify(transformed),
                })

                console.log(response);
            },
        },
    };
</script>
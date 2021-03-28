<template>
    <div>
        <div class="grid grid-cols-1 md:grid-cols-2" style="grid-auto-rows: 4.5rem">
            <Property
                v-for="prop in present_properties"
                :key="prop.label"
                :property="prop"
                :data="modelValue"
                @update:data="handleChange(prop, $event)"
                permissionLevel="supervisor"
                :editing="editing"
            />
            <!--
                :label="prop.label"
                :modelValue="this.modelValue[prop.key]"
                @update:modelValue="handleChange(prop, $event)"
                :component="prop.component"
                :editor="prop.editor"
                :editing="isEditable(prop)"
                :required="prop.required"
                :description="prop.description"
                removable
            />-->
        </div>

        <!--<button
            v-if="absent_properties.length > 0"
            class="border-2 border-blue-400 px-2 py-1 rounded-sm"
            @click="showPropertyDialog()"
        >
            Add Field
        </button>-->

        <teleport to="body">
            <Dialog
                header="Add Field"
                v-if="addFieldDialogVisible"
                @close="addFieldDialogVisible = false"
            >
                <div class="py-2">
                    <h4 class="mb-3">The following additional properties are available:</h4>
                    <div
                        v-for="prop in absent_properties"
                        :key="prop.label"
                        @click="addProperty(prop)"
                        class="p-2 mb-1 hover:bg-gray-100 rounded-md cursor-pointer"
                    >
                        <span>{{ prop.label }}</span>
                        <div class="text-gray-500 text-sm">{{ prop.description }}</div>
                    </div>
                </div>
            </Dialog>
        </teleport>
    </div>
</template>

<script>
    import { SELF_EDITABLE, SUPERVISOR_EDITABLE } from '../models/user.js';

    import Property from './UserProperty.vue';
    import Dialog from './Dialog.vue';

    function isEmpty(value) {
        return value === null || value === undefined;
    }

    export default {
        components: { Property, Dialog },

        emits: ['additionalPropertiesAvailable', 'propertyChange', 'update:modelValue'],

        props: ['model', 'modelValue', 'permissionLevel', 'editing'],

        data () {
            return {
                addFieldDialogVisible: false,
            };
        },

        methods: {
            handleChange (prop, value) {
                this.$emit('update:modelValue', {
                    ... this.modelValue,
                    [ prop.key ]: value,
                });

                this.$emit('propertyChange', { property: prop, value });
            },

            isEditable (prop) {
                const order = [ SELF_EDITABLE, SUPERVISOR_EDITABLE ];

                return !isEmpty(this.permissionLevel) && order.indexOf(this.permissionLevel) >= order.indexOf(prop.editable);
            },

            addProperty (prop) {
                this.handleChange(prop, prop.defaultValue || '');
                this.addFieldDialogVisible = false;
            },

            showPropertyDialog () {
                this.addFieldDialogVisible = true;
            },

            additionalPropertiesExist () {
                return this.absent_properties.length > 0;
            },
        },

        mounted () {
            this.$emit('additionalPropertiesAvailable', this.absent_properties);
        },

        watch: {
            absent_properties () {
                this.$emit('additionalPropertiesAvailable', this.absent_properties);
            },
        },

        computed: {
            present_properties () {
                return Object.values(this.model)
                    .filter(({ key }) => !isEmpty(this.modelValue[key]));
            },

            absent_properties () {
                return Object.values(this.model)
                    .filter((prop) => isEmpty(this.modelValue[prop.key]) && this.isEditable(prop));
            },
        },
    }
</script>
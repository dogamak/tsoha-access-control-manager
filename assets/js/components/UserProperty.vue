<script>
    import { h, defineComponent } from 'vue';

    import Button from './Button.vue';

    const PERMISSION_ORDER = ['self', 'supervisor'];

    export default {
        emits: ['update:data'],

        props: {
            data: {
                type: Object,
                required: true,
            },
            property: {
                type: Object,
                required: true,
                validator: (value) => ['key', 'label'].findIndex((key) => !value[key]) === -1,
            },
            permissionLevel: {
                type: String,
                validator: (value) => ['supervisor', 'self'].indexOf(value) !== -1,
            },
            editing: Boolean,
        },

        render () {
            let fragment;
            let activeComponent = null;

            if (!this.property)
                return null;

            if (this.isEditable && this.editing) {
                if (this.property && this.property.editor) {
                    activeComponent = this.property.editor;

                    fragment = h(this.property.editor, {
                        modelValue: this.value,
                        'onUpdate:modelValue': (value) => this.$emit('update:data', value),
                        'onRemove': () => this.$emit('update:data', undefined),
                    });
                } else {
                    fragment = h('input', {
                        class: 'bg-gray-100 mr-6 py-1 px-3 text-gray-900 border-2 border-gray-100 outline-none focus:border-blue-400 mt-1 rounded-sm',
                        value: this.value,
                        type: 'text',
                        onInput: (evt) => this.$emit('update:data', evt.target.value),
                    });
                }
            } else {
                if (this.property && this.property.component) {
                    activeComponent = this.property.component;

                    fragment = h(this.property.component, {
                        value: this.value,
                        'onRemove': () => this.$emit('update:data', undefined),
                    });
                } else {
                    fragment = h('span', [this.value]);
                }
            }

            let remove = null;

            if (
                this.editing && this.isRemovable && (
                    activeComponent === null || !activeComponent.getProperties || (
                        typeof activeComponent.getProperties === 'function' &&
                        !activeComponent.getProperties().hideRemoveButton
                    )
                )
            ) {
                remove = h(
                    Button,
                    {
                        tertiary: true,
                        onClick: () => this.$emit('update:data', undefined),
                    },
                    ['Remove'],
                );
            }

            let help = null;

            if (this.property && this.property.description) {
                help = (
                    <span title={ this.property.description } class="border-2 opacity-0 group-hover:opacity-100 inline-block w-3 h-3 rounded-full" style="border-width: 1px;border-color: #d3cdcd;font-size: 0.6rem;text-align: center;transform: translate(0%, 10%);cursor: help;">
                        <span style="transform: translate(0%, -15%);display: inline-block;color: #d3cdcd;">?</span>
                    </span>
                );
            }

            let errorEl = null;

            if (this.value && this.property.validator) {
                let errorMessage = this.property.validator(this.value);

                if (errorMessage) {
                    errorEl = (
                        <span title={ errorMessage } class="border-2 inline-block w-3 h-3 rounded-full" style="border-width: 1px;border-color: rgb(220, 38, 38);color: rgb(220, 38, 38);font-size: 0.6rem;text-align: center;transform: translate(0%, 10%);cursor: help;margin-right: 0.2rem;">
                            <span style="transform: translate(0%, -15%);display: inline-block;">!</span>
                        </span>
                    );
                }
            }

            let rowSpan = 1;
            let colSpan = 1;

            if (activeComponent !== null && typeof activeComponent.getProperties === 'function') {
                const { width, height } = activeComponent.getProperties();

                rowSpan = height;
                colSpan = width;
            }

            return (
                <div class={`w-fill px-3 mb-3 md:col-span-${colSpan} row-span-${rowSpan} inline-flex flex-col whitespace-nowrap group`}>
                    <div class="text-gray-500 text-xs flex items-center">
                        <label class={ errorEl ? 'text-red-600' : '' } style="margin-right: 0.25rem">{ this.property.label }</label>
                        { errorEl }
                        { help }
                    </div>
                    <div class="flex flex-grow">
                        <div class="flex-grow">
                            { fragment }
                        </div>
                        { remove }
                    </div>
                </div>
            );
        },

        methods: {
            onChange (value) {
                this.$emit('update:data', value);
            },
        },

        computed: {
            isEditable () {
                if (!this.property)
                    return false;

                return PERMISSION_ORDER.indexOf(this.permissionLevel) >= PERMISSION_ORDER.indexOf(this.property.editable);
            },

            isRemovable () {
                return this.isEditable && !this.property.required;
            },

            value () {
                if (!this.property)
                    return null;

                return this.data[this.property.key];
            },
        },
    };
</script>
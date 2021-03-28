<template>
    <div class="flex h-full" data-ref="root" style="min-height: 7rem">
        <div ref="photo_wrapper" class="h-full">
            <div
                class="flex flex-col bg-gray-100 gap-5 items-center justify-center rounded-sm p-5 bg-cover bg-center"
                :style="this.photoStyles + (this.modelValue ? `background-image: url('${ this.modelValue.url }')` : '')"
            >
                <span class="text-gray-600" :style="`opacity: ${this.modelValue ? 0 : 1}`">No Photo</span>
            </div>
        </div>
        <div ref="controls_wrapper" data-ref="controls" class="pl-3">
            <Button :label="modelValue ? 'Change' : 'Upload'" @click="selectFile" />
            <br />
            <Button label="Remove" class="mt-1" tertiary @click="$emit('remove')" />
        </div>
    </div>
</template>

<script>
    import Button from './Button.vue';

    export default {
        components: { Button },

        props: ['modelValue'],

        emits: ['update:modelValue', 'remove'],

        data () {
            return {
                progress: 0.6,
                photoStyles: '',
            };
        },

        mounted () {
            const sizeCache = {};

            const observer = new ResizeObserver((entries) => {
                entries.forEach((entry) => sizeCache[entry.target.getAttribute('data-ref')] = entry);

                let { bottom, right } = sizeCache.root.contentRect;
                right -= sizeCache.controls.contentRect.right;

                let size = bottom < right ? bottom : right;

                this.photoStyles = `
                    width: ${size}px;
                    height: ${size}px;
                `;

                console.log(this.photoStyles);
                console.log(sizeCache);
            });

            observer.observe(this.$el);
            observer.observe(this.$refs.photo_wrapper);
            observer.observe(this.$refs.controls_wrapper);
        },

        methods: {
            selectFile () {
                const input = document.createElement('input');
                input.setAttribute('type', 'file');

                input.addEventListener('change', () => this.handleFile(input), false);

                input.click();
            },

            handleFile (input) {
                const file = input.files[0];
                console.log(file);
                this.$emit('update:modelValue', { url: window.URL.createObjectURL(file) });
            },
        },

        getProperties () {
            return {
                width: 1,
                height: 2,
                hideRemoveButton: true,
            };
        },

        computed: {
            photoStyles () {
                if (this.modelValue === null || this.modelValue === undefined) {
                    return ''
                }
            },
        },
    };
</script>
<template>
    <div class="flex h-full" data-ref="root" style="min-height: 7rem">
        <div ref="photo_wrapper" class="h-full">
            <div
                class="flex flex-col bg-gray-100 gap-5 items-center justify-center rounded-sm p-5 bg-cover bg-center"
                :style="this.photoStyles + (this.modelValue ? `background-image: url('${ this.modelValue }')` : '')"
            >
                <span class="text-gray-600" :style="`opacity: ${this.modelValue ? 0 : 1}`">No Photo</span>
            </div>
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

            const observer = new ResizeObserver(([ root ]) => {
                let { bottom, right } = root.contentRect;

                let size = bottom < right ? bottom : right;

                this.photoStyles = `
                    width: ${size}px;
                    height: ${size}px;
                `;
            });

            observer.observe(this.$el);
        },

        getProperties () {
            return {
                width: 1,
                height: 2,
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
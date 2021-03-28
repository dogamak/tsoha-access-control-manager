<template>
    <button :class="classes"><slot>{{ label }}</slot></button>
</template>

<script>
    const COMMON = ['border-2', 'font-bold', 'hover:shadow-inner', 'rounded-sm', 'px-3', 'py-1', 'shadow-md'];

    const COMMON_STYLES = {
        secondary: COMMON,
        primary: COMMON,
        tertiary: ['text-sm'],
    };

    const STYLES = {
        normal: {
            secondary: ['border-gray-400', 'bg-gray-100', 'text-gray-500'],
            primary: ['border-blue-500', 'bg-blue-500', 'text-white'],
            tertiary: ['text-gray-500'],
        },
        dangerous: {
            secondary: ['border-red-600', 'bg-white', 'text-red-600'],
            primary: ['border-red-600', 'bg-red-600', 'text-white'],
            tertiary: ['text-red-600'],
        },
    };

    export default {
        props: {
            label: {
                type: String,
                required: true,
            },
            primary: Boolean,
            dangerous: Boolean,
            tertiary: Boolean,
        },

        computed: {
            classes () {
                const variant = this.dangerous ? 'dangerous' : 'normal';

                let level = 'secondary';
                
                if (this.primary) {
                    level = 'primary';
                } else if (this.tertiary) {
                    level = 'tertiary';
                }

                return [ ...COMMON_STYLES[level], ...STYLES[variant][level] ];
            },
        },
    };
</script>
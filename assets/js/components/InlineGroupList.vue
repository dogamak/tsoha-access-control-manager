<template>
    <div>
        <div v-for="group in modelValue" :key="group.id">
            <span>{{ group.name }}</span>
        </div>
    </div>
</template>

<script>
    export default {
        props: ['modelValue'],
    };
</script>
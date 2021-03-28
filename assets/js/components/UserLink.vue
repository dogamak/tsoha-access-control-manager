<template>
    <a class="text-blue-500" :href="$url_for('user_details', { username: user.username })">{ user.name || user.username }</a>
</template>

<script>
    export default {
        props: ['user'],
    };
</script>
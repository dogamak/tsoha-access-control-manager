let router = null;

export function url_for(endpoint, args) {
    if (router === null) {
        router = eval('(' + window._bootstrap_data.router + ')');
    }

    return router[endpoint](args);
}

export function navigate(endpoint, args) {
    window.location = url_for(endpoint, args);
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);

    if (parts.length === 2)
        return parts.pop().split(';').shift();
}

export default {
    install (app) {
        app.config.globalProperties.$url_for = url_for;
        app.config.globalProperties.$navigate = navigate;
        app.config.globalProperties.$user = window._bootstrap_data.user;
        app.config.globalProperties.$csrf_token = getCookie('csrf_access_token');

        app.provide('all_groups', window._bootstrap_data.groups || []);
        app.provide('all_users', window._bootstrap_data.users || []);
    }
};
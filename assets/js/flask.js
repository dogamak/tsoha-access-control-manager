function url_for(endpoint, args) {
    return window._flask_routes[endpoint](args);
}

function navigate(endpoint, args) {
    window.location = url_for(endpoint, args);
}

export default {
    install (app) {
        app.config.globalProperties.$url_for = url_for;
        app.config.globalProperties.$navigate = navigate;
        app.config.globalProperties.$user = window._current_user;
    }
};
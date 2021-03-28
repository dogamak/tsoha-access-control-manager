import { createApp, h } from 'vue';
import flask from './flask.js';

import Main from './components/Main.vue';

export function init(component) {
    const app = createApp({
        render: () => h(Main, { breadcrumb: window._bootstrap_data.breadcrumb },
            () => h(component, window._bootstrap_data.props)
        ),
    });

    app.use(flask);

    app.mount('#main');
}
import { createApp, h } from 'vue';
import flask from './flask.js';

import Main from './components/Main.vue';

export function init(component) {
    const app = createApp({
        render: () => h(Main, {},
            () => h(component, window._page_props)
        ),
    });

    app.use(flask);

    app.mount('#main');
}
import Vue from 'vue';
import * as ModalDialogs from 'vue-modal-dialogs';

import Editor from './components/editor/Editor.vue';

Vue.use(ModalDialogs);

new Vue({
  el: '#editor',
  render: (h) => h(Editor),
});

import vue from 'rollup-plugin-vue';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import { babel } from '@rollup/plugin-babel';
import replace from '@rollup/plugin-replace';

export default {
  input: 'assets/js/editor.js',

  output: {
    file: 'dist/js/editor.bundle.js',
    sourcemap: 'inline',
  },

  plugins: [
    nodeResolve(),
    vue(),
    babel({ babelHelpers: 'bundled' }),
    replace({
      'process.env.NODE_ENV': JSON.stringify('development')
    })
  ],
};

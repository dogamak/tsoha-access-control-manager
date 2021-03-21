import vue from 'rollup-plugin-vue';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import { babel } from '@rollup/plugin-babel';
import replace from '@rollup/plugin-replace';
import autoprefixer from 'autoprefixer';
import glob from 'glob';
import path from 'path';
import postcss from 'rollup-plugin-postcss';
import tailwindcss from 'tailwindcss';

const plugin = (component) => ({
  name: 'custom-plugin',

  resolveId (source) {
    if (source === 'entrypoint') {
      return source;
    }

    return null
  },

  load (id) {
    if (id === 'entrypoint') {
      return `
        import { init } from './assets/js/bootstrap.js';
        import PageComponent from './${component}';

        init(PageComponent);
      `;
    }

    return null;
  },
});

const config = (component) => {
  const basename = path.basename(component);
  const ext = path.extname(basename);
  const name = basename.substring(0, basename.length - ext.length);

  return {
    input: 'entrypoint',

    output: {
      file: `dist/js/${name}.bundle.js`,
      sourcemap: 'inline',
    },

    plugins: [
      plugin(component),
      nodeResolve(),
      vue(),
      postcss([
        autoprefixer,
        tailwindcss('tailwind.config.js'),
      ]),
      babel({ babelHelpers: 'bundled' }),
      replace({
        'process.env.NODE_ENV': JSON.stringify('development')
      })
    ],
  };
};

const options = glob.sync('assets/js/components/pages/**/*.vue').map(config);
console.log(options);

export default options;
const glob = require('glob');
const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractLoader = require('mini-css-extract-plugin');

const page_files = glob.sync('assets/js/components/pages/**/*.vue');

const entry = {};
const plugins = [];

for (const page_file of page_files) {
  const basename = path.basename(page_file);
  const ext = path.extname(basename);
  const name = basename.substring(0, basename.length - ext.length);

  entry[name] = './page_loader.js!' + path.resolve(page_file);
  
  plugins.push(new HtmlWebpackPlugin({
    template: './template.ejs',
    filename: 'templates/' + name + '.html',
    publicPath: '/build',
    chunks: [name],
    scriptLoading: 'blocking',
  }));
}

module.exports = {
    entry,

    output: {
        path: path.resolve(__dirname, 'build'),
        filename: 'js/[name].bundle.js',
    },

    module: {
      rules: [
        {
          test: /\.vue$/,
          use: 'vue-loader',
        },
        {
          test: /\.css$/,
          use: [
            'vue-style-loader',
            {
              loader: MiniCssExtractLoader.loader,
              options: {
                esModule: false,
              },
            },
            {
              loader: 'css-loader',
              options: {
                //modules: true,
              },
            },
            'postcss-loader',
          ],
        },
        {
          test: /\.s[ac]ss$/,
          use: [
            'vue-style-loader',
            {
              loader: MiniCssExtractLoader.loader,
              options: {
                esModule: false,
              },
            },
            {
              loader: 'css-loader',
              options: {
                // modules: true,
              },
            },
            'postcss-loader',
            'sass-loader',
          ],
        },
      ],
    },

    mode: 'development',
    devtool: 'eval-source-map',

    optimization: {
      minimize: false,
      splitChunks: {
        chunks: 'all',
      },
    },

    plugins: [
      new VueLoaderPlugin(),
      new MiniCssExtractLoader({
        filename: 'css/[name].css',
      }),
      ...plugins,
    ],
};
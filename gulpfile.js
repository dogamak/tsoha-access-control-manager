const gulp = require('gulp');
const sass = require('gulp-sass');
const postcss = require('gulp-postcss');
const tailwindcss = require('tailwindcss');
const autoprefixer = require('autoprefixer');
const path = require('path');
const Vinyl = require('vinyl');

const rollup = require('gulp-rollup');
const through = require('through2');

gulp.task('css', function () {
  return gulp.src('assets/css/**/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss([
      tailwindcss('tailwind.config.js'),
      autoprefixer,
    ]))
    .pipe(gulp.dest('dist/css'));
});

function generateEntrypoints (entrypoints) {
  return through.obj(function (file, encoding, callback) {
    console.log(file.path);
    const basename = path.basename(file.path);
    const ext = path.extname(basename);
    const name = basename.substring(0, basename.length - ext.length);

    if (file.path.indexOf('pages') === -1 || ext !== '.vue')
      return callback(null, file);

    const entrypoint_path = path.join(file.base, `${name}.entry${ext}`);

    this.push(new Vinyl({
      cwd: file.cwd,
      base: file.base,
      path: entrypoint_path,
      contents: Buffer.from(`
        import Vue from 'vue';
        import PageComponent from '${ file.path }';

        new Vue({
          el: '#main',
          render: (h) => h(Main),
          propsData: {
            page: PageComponent,
          },
        });
      `),
    }));

    entrypoints.push(entrypoint_path);

    callback(null, file);
  });
}

gulp.task('vue', function () {
  const entrypoints = [];

  return gulp.src('assets/js/**/*')
    .pipe(generateEntrypoints(entrypoints))
    .pipe(rollup({
      input: entrypoints,
    }))
    .pipe(gulp.dest('dist/js/pages'));
});
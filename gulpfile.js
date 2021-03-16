const gulp = require('gulp');
const sass = require('gulp-sass');
const postcss = require('gulp-postcss');
const tailwindcss = require('tailwindcss');
const autoprefixer = require('autoprefixer');

gulp.task('css', function () {
  return gulp.src('assets/css/**/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss([
      tailwindcss('tailwind.config.js'),
      autoprefixer,
    ]))
    .pipe(gulp.dest('dist/css'));
});

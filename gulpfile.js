/* jshint esversion: 6 */
const gulp = require('gulp');
const browserSync = require('browser-sync');
const sass = require('gulp-sass');
const postcss = require('gulp-postcss');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');
const del = require('del');
const concat = require('gulp-concat');
const uglify = require('gulp-uglify');
const argv = require('yargs').argv;

const DESTINATION = 'ubio/static';
const SOURCE = 'frontend';

const paths = {
    styles: {
        source: `${SOURCE}/scss/*.scss`,
        destination: `${DESTINATION}/css`
    },
    scripts: {
        source: `${SOURCE}/**/*.js`,
        destination: `${DESTINATION}/scripts`
    },
    html: {
        source: `${SOURCE}/**/*.html`
        // destination: `${DESTINATION}/`
    },
    images: {
        source: `${SOURCE}/images/*`,
        destination: `${DESTINATION}/images`
    }
};

function styles() {
    return gulp.src(paths.styles.source)
        .pipe(sass()).on("error", sass.logError)
        // .pipe(postcss([autoprefixer(), cssnano()]))
        .pipe(gulp.dest(paths.styles.destination))
        .pipe(browserSync.stream());
}

function scripts() {
    return gulp.src(paths.scripts.source)
        .pipe(concat('app.min.js'))
        // .pipe(uglify())
        .pipe(gulp.dest(paths.scripts.destination))
        .pipe(browserSync.stream());
}

function html(cb) {
    if (!argv.production) {
        return gulp.src(paths.html.source)
            // .pipe(gulp.dest(paths.html.destination))
            .pipe(browserSync.stream());
    }
    cb();
}

function images() {
    return gulp.src(paths.images.source)
      .pipe(gulp.dest(paths.images.destination))
      .pipe(browserSync.stream());
}

function clean(cb) {
    del([`${paths.styles.destination}`]);
    del([`${paths.scripts.destination}`]);
    // del([`${paths.html.destination}`]);
    cb();
}

function serve() {
    browserSync.init({server: [`${DESTINATION}`, `${SOURCE}/samples`]});
    gulp.watch(paths.styles.source, styles);
    gulp.watch(paths.scripts.source, scripts);
    gulp.watch(paths.html.source, html);
    gulp.watch(paths.images.source, images);
}

const build = gulp.parallel(styles, scripts, images);

exports.build = build;
exports.clean = clean;
exports.serve = serve;
exports.default = gulp.series(clean, build, serve);

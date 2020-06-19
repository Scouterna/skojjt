// noinspection ES6ConvertRequireIntoImport
const gulp = require('gulp');
// noinspection ES6ConvertRequireIntoImport
const plug = {
    babel: require('gulp-babel'),
    concat: require('gulp-concat'),
    debug: require('gulp-debug'),
    flatmap: require('gulp-flatmap'),
    htmlmin: require('gulp-htmlmin'),
    imagemin: require('gulp-imagemin'),
    less: require('gulp-less'),
    rename: require('gulp-rename'),
    sourcemaps: require('gulp-sourcemaps'),
    typescript: require('gulp-typescript'),
    uglifycss: require('gulp-clean-css'),
    uglifyjsES: require('gulp-uglify-es').default,
    uglifyjs: require('gulp-uglify'),
    watch: require('gulp-watch'),
};
const imageminPlugins = {
    optipng: require("imagemin-optipng"),
};

const htmlPath = 'html/**/*.html';
const imgPath = 'img/**/*';
const lessPath = 'less/**/*.less';
const typeScriptPath = 'ts/**/*.ts';

const uglifyCssOptions = {
    level: {
        2: {
            mergeSemantically: true,
            restructureRules: true,
        }
    }
};

//<editor-fold desc="Typescript">
//<editor-fold desc="Typescript ES5">
const tsEs5 = (s) => s
    .pipe(plug.sourcemaps.init())
    .pipe(plug.typescript.createProject({
        "target": "ES5",
        "lib": ["DOM", "ES5", "ScriptHost", "ES2015.Promise", "ES2015.Iterable"]
    })())
    .pipe(plug.concat('es5.js'))
    .pipe(plug.babel({
        compact: false,
        presets: [["@babel/env", {
            "targets": {
                "browsers": ["cover 95% in se, not dead"],
            },
        }]],
    }))
    .pipe(plug.uglifyjs())
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/ts/'}))
    .pipe(gulp.dest('../build/'))
    .pipe(plug.debug({title: 'ts-es5:'}));
//</editor-fold>
//<editor-fold desc="Typescript ES6">
const tsEs6 = (s) => s
    .pipe(plug.sourcemaps.init())
    .pipe(plug.typescript.createProject({"target": "ES6", "lib": ["DOM", "ES6", "ScriptHost", "DOM.Iterable"]})())
    .pipe(plug.concat('es6.js'))
    .pipe(plug.babel({
        compact: false,
        presets: [["@babel/env", {
            "targets": {
                browsers: [
                    'last 2 Chrome versions',
                    'last 2 Safari versions',
                    'last 2 Firefox versions',
                    'last 2 Edge versions',
                ],
            },
        }]],
    }))
    .pipe(plug.uglifyjsES())
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: "../src/ts/"}))
    .pipe(gulp.dest('../build/'))
    .pipe(plug.debug({title: 'ts-es6:'}));
//</editor-fold>
const tsEs5Task = () => tsEs5(gulp.src(typeScriptPath));
const tsEs6Task = () => tsEs6(gulp.src(typeScriptPath));
gulp.task("ts-es5", tsEs5Task);
gulp.task("ts-es6", tsEs6Task);
gulp.task("ts", gulp.parallel(["ts-es5", "ts-es6"]));

//<editor-fold desc="Typescript watch">
// noinspection ChainedFunctionCallJS
const tsEs5Wwatch = () => plug
    .watch(typeScriptPath)
    .pipe(plug.debug({title: 'watch-es5:'}))
    .pipe(plug.flatmap(tsEs5));
const tsEs6Watch = () => plug
    .watch(typeScriptPath)
    .pipe(plug.debug({title: 'watch-es6:'}))
    .pipe(plug.flatmap(tsEs6));
gulp.task("ts-watch-es5", tsEs5Wwatch);
gulp.task("ts-watch-es6", tsEs6Watch);
/// TODO gulp watch
gulp.task("ts-watch", gulp.parallel(["ts-watch-es5", "ts-watch-es6"]));
//</editor-fold>
//</editor-fold>

//<editor-fold desc="LESS">
const lessMain = (s) => s
    .pipe(plug.sourcemaps.init())
    .pipe(plug.less())
    .pipe(plug.concat('style.css'))
    .pipe(plug.uglifycss(uglifyCssOptions))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/less/'}))
    .pipe(gulp.dest('../build/'))
    .pipe(plug.debug({title: 'less:'}));
const lessTask = () => lessMain(gulp.src(lessPath));
const lessWatch = () => lessMain(plug
    .watch(lessPath)
    .pipe(plug.debug({title: 'watch:'})));
gulp.task("less", lessTask);
gulp.task("less-watch", lessWatch);
//</editor-fold>

//<editor-fold desc="Images">
const imgMain = (s) => s
    .pipe(plug.imagemin({
        progressive: true,
        use: [
            imageminPlugins.optipng
        ]
    }))
    .pipe(gulp.dest('../build/'))
    .pipe(plug.debug({title: 'img:'}));
const imgTask = () => imgMain(gulp.src(imgPath));
const imgWatch = () => imgMain(plug
    .watch(imgPath)
    .pipe(plug.debug({title: 'watch:'})));
gulp.task('images', imgTask);
gulp.task('images-watch', imgWatch);
//</editor-fold>

//<editor-fold desc="HTML">
// noinspection ChainedFunctionCallJS
const htmlMain = (s) => s
    .pipe(plug.sourcemaps.init())
    .pipe(plug.htmlmin({
        collapseWhitespace: true,
        removeComments: true,
        sortAttributes: true,
        sortClassName: true,
    }))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/html/'}))
    .pipe(gulp.dest('../build/'))
    .pipe(plug.debug({title: 'html:'}));
const htmlTask = () => htmlMain(gulp.src(htmlPath));
const htmlWatch = () => htmlMain(plug
    .watch(htmlPath)
    .pipe(plug.debug({title: 'watch:'})));
gulp.task("html", htmlTask);
gulp.task("html-watch", htmlWatch);
//</editor-fold>

gulp.task("all", gulp.parallel(['ts', 'less', 'html', 'images']));
gulp.task("default", gulp.parallel(['ts', 'less', 'html']));
gulp.task("watch", gulp.series(["default", gulp.parallel(['ts-watch', 'less-watch', 'html-watch', 'images-watch'])]));

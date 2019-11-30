"use strict";
const gulp = require("gulp");
const plug = {
    babel: require("gulp-babel"),
    chmod: require("gulp-chmod"),
    concat: require("gulp-concat"),
    debug: require('gulp-debug'),
    flatmap: require("gulp-flatmap"),
    ignore: require("gulp-ignore"),
    imagemin: require("gulp-imagemin"),
    less: require("gulp-less"),
    plumber: require("gulp-plumber"),
    pngquant: require("gulp-pngquant"),
    rename: require("gulp-rename"),
    sourcemaps: require("gulp-sourcemaps"),
    typescript: require("gulp-typescript"),
    uglifyCss: require("gulp-clean-css"),
    uglifyJs: require("gulp-uglify"),
};

// Compile less to css and minify it.
const lessTask = () => gulp
    .src(["less/**/*.less"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(plug.less())
    .pipe(plug.uglifyCss())
    .pipe(plug.rename({suffix: ".min"}))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/less/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/css/"));

// Plain css, but still minify it.
const cssTask = () => gulp
    .src(["css/**/*.css"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(plug.uglifyCss())
    .pipe(plug.rename({suffix: ".min"}))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/css/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/css/"));

// Compile typescript to js and minify it.
const typescriptTask = () => gulp
    .src(["ts/**/*.ts"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init())
    .pipe(plug.flatmap(
        (stream /*, file */) => stream.pipe(
            plug.typescript.createProject(
                {
                    "target": "ES5",
                    "lib": [
                        "DOM",
                        "ES5",
                        "ScriptHost",
                        "ES2015.Promise",
                        "ES2015.Iterable",
                    ]
                })(),
            ""
        ),
    ))
    .pipe(plug.uglifyJs())
    .pipe(plug.rename({ suffix: ".min" }))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/ts/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/js/"));;

// Babel the javascript and minify it.
const javascriptTask = () =>  gulp
    .src(["js/**/*.js"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(
        plug.babel({
            compact: false,
            presets: [[
                "@babel/env", {
                    "targets": {
                        "browsers": [
                            ">0.25%"
                        ],
                    },
                }
            ]],
        }))
    .pipe(plug.uglifyJs())
    .pipe(plug.rename({suffix: ".min"}))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/js/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/js"));

const img_task = () => gulp
	.src('img/**/*')
	.pipe(plug.imagemin({
		progressive: true,
		use: [plug.pngquant()]
	}))
	.pipe(gulp.dest('../build/img/'));

gulp.task("css", cssTask);
gulp.task("less", lessTask);
gulp.task("js", javascriptTask);
gulp.task("ts", typescriptTask);
gulp.task("img", img_task);

gulp.task("default", gulp.parallel("css", "less", "js", "ts"));
gulp.task("all", gulp.parallel("default", "img"));

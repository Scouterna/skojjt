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
const mainLessTask = () => gulp
    .src(["less/main/**/*.less"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(plug.less())
    .pipe(plug.concat("main.less.css"))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/less/main/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/css/"));

// Compile less to css and minify it.
const pageLessTask = () => gulp
    .src(["less/pages/**/*.less"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(plug.less())
    .pipe(plug.uglifyCss())
    .pipe(plug.rename({suffix: ".min"}))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/less/pages/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/css/"));

// Plain main css, concat and minify it.
const mainCssTask = () => gulp
    .src(["css/main/**/*.css", "../build/css/main.less.css"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(plug.uglifyCss())
    .pipe(plug.concat("main.min.css"))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/css/main/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/css/"));

// Plain page css, minify it.
const pageCssTask = () => gulp
    .src(["css/pages/**/*.css"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init({loadMaps: true}))
    .pipe(plug.uglifyCss())
    .pipe(plug.rename({suffix: ".min"}))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/css/pages/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/css/"));

// Compile page typescript to js and minify it.
const pageTypescriptTask = () => gulp
    .src(["ts/pages/**/*.ts"])
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
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/ts/pages/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/js/"));;

// Compile main typescript to js, concat and use it in main-js.
const mainTypescriptTask = () => gulp
    .src(["ts/main/**/*.ts"])
    .pipe(plug.plumber())
    .pipe(plug.sourcemaps.init())
    .pipe(
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
            }
        )()
    )
    .pipe(plug.concat("main.ts.js"))
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/ts/main/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/js/"));;

// Babel the javascript and minify main scripts.
const mainJavascriptTask = () =>  gulp
    .src(["js/main/**/*.js", "../build/js/main.ts.js"])
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
    .pipe(plug.concat('main.min.js'))
    .pipe(plug.uglifyJs())
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/js/main/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/js"));

// Babel the javascript and minify pages.
const pageJavascriptTask = () =>  gulp
    .src(["js/pages/**/*.js"])
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
    .pipe(plug.sourcemaps.write("./", {includeContent: false, sourceRoot: '../src/js/pages/'}))
    .pipe(plug.chmod(0o644))
    .pipe(gulp.dest("../build/js"));

// omptimize images
const img_task = () => gulp
	.src('img/**/*')
	.pipe(plug.imagemin({
		progressive: true,
		use: [plug.pngquant()]
	}))
	.pipe(gulp.dest('../build/img/'));

gulp.task("main-less", mainLessTask);
gulp.task("page-less", pageLessTask);
gulp.task("less", gulp.parallel("main-less", "page-less"));
gulp.task("main-css", mainCssTask);
gulp.task("page-css", pageCssTask);
gulp.task("plain-css", gulp.parallel("main-css", "page-css"));
gulp.task("css", gulp.series("less", "plain-css"));

gulp.task("main-ts", mainTypescriptTask);
gulp.task("page-ts", pageTypescriptTask);
gulp.task("ts", gulp.parallel("main-ts", "page-ts"));
gulp.task("main-js", mainJavascriptTask);
gulp.task("page-js", pageJavascriptTask);
gulp.task("plain-js", gulp.parallel("main-js", "page-js"));
gulp.task("js", gulp.series("ts", "plain-js"));

gulp.task("img", img_task);

gulp.task("default", gulp.parallel("css", "js"));
gulp.task("all", gulp.parallel("default", "img"));

const webpack         = require ('webpack');
const path            = require ('path');
const VueLoaderPlugin = require ('vue-loader/lib/plugin');
const precss          = require ('precss');
const autoprefixer    = require ('autoprefixer');

module.exports = {
    entry : {
        app : 'js/main.js', // in app.bundle.js
    },
    output : {
        filename : 'js/[name].bundle.js',
        path : path.resolve (__dirname, 'build'),
    },
    module : {
        rules : [
            {
                test : /\.js$/,
                exclude : /node_modules/,
                use : [
                    'babel-loader',
                ],
            },
            {
                test: /\.vue$/,
                exclude: /node_modules/,
                use: [
                    'vue-loader',
                ],
            },
            {
                test: /\.css$/,
                use: [
                    'vue-style-loader',
                    'css-loader',
                ],
            },
            {
                test: /\.scss$/,
                use: [
                    'vue-style-loader',
                    'css-loader',
                    {
                        loader: 'postcss-loader',
                        options: {
                            plugins: function () { // post css plugins, can be exported to postcss.config.js
                                return [
                                    precss,
                                    autoprefixer,
                                ];
                            },
                        },
                    },
                    'sass-loader',
                ],
            },
            {
                test: /\.less$/,
                use: [
                    'vue-style-loader',
                    'css-loader',
                    {
                        loader: 'postcss-loader',
                        options: {
                            plugins: function () { // post css plugins, can be exported to postcss.config.js
                                return [
                                    precss,
                                    autoprefixer,
                                ];
                            },
                        },
                    },
                    {
                        loader: 'less-loader',
                        options: {
                            globalVars : {
                                BS : "'" + path.resolve (__dirname, 'node_modules/bootstrap/less') + "'",
                            },
                        },
                    },
                ],
            },
            {
                test: /\.(png|jpg|jpeg|gif)$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: '/images/[name].[ext]',
                        },
                    },
                ],
            },
            {
                test: /\.(eot|svg|ttf|woff|woff2)$/,
                use: [
                    {
                        loader: 'file-loader',
                        options: {
                            name: '/webfonts/[name].[ext]',
                        },
                    },
                ],
            },
            {
                // compile a pegjs grammar to js
                test: /\.pegjs$/,
                use: [
                    'pegjs-loader',
                ],
            },
        ],
    },
    plugins: [
        new VueLoaderPlugin (),
        // new ExtractTextPlugin('bundle.styles.css'),
        new webpack.ProvidePlugin ({
            // inject ES5 modules as global vars mainly for bootstrap 3
            '$'            : 'jquery',
            'jQuery'       : 'jquery',
            'window.jQuery': 'jquery',
        }),
    ],
    optimization: {
        splitChunks: {
            cacheGroups: {
                common: {
                    name: 'common',
                    chunks: 'all',
                    minChunks: 2,
                    enforce: true,
                },
                vendor: {
                    name: 'vendor',
                    test: /node_modules/,
                    chunks: 'all',
                    reuseExistingChunk: true,
                },
            },
        },
        runtimeChunk: 'single',
    },
    resolve: {
        modules: [
            path.resolve (__dirname, 'src'),
            path.resolve (__dirname, 'src/js'),
            path.resolve (__dirname, 'src/less'),
            path.resolve (__dirname, 'src/components'),
            'node_modules',
        ],
        alias: {
            /* See: https://webpack.js.org/configuration/resolve/#resolve-alias */
            'vue$' : path.resolve (__dirname, 'node_modules/vue/dist/vue.esm.js'),
            'bootstrap.css' : path.resolve (__dirname, 'node_modules/bootstrap/dist/css/bootstrap.css'),
            'bootstrap-slider.css' : path.resolve (
                __dirname, 'node_modules/bootstrap-slider/dist/css/bootstrap-slider.css'
            ),
            'datatables.net-bs.css' : path.resolve (
                __dirname, 'node_modules/datatables.net-bs/css/dataTables.bootstrap.css'
            ),
            'datatables.net-buttons-bs.css' : path.resolve (
                __dirname, 'node_modules/datatables.net-buttons-bs/css/buttons.bootstrap.css'
            ),
            'jquery-ui'      : path.resolve (__dirname, 'node_modules/jquery-ui/ui/widgets'),
            'jquery-ui-css'  : path.resolve (__dirname, 'node_modules/jquery-ui/themes/base'),
            'd3'             : path.resolve (__dirname, 'node_modules/d3/dist/d3.js'),
        },
    },
};

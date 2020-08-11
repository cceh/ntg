const path            = require ('path');
const VueLoaderPlugin = require ('vue-loader/lib/plugin');

module.exports = {
    entry : {
        app : 'js/app.js', // in app.bundle.js
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
                    {
                        loader: 'css-loader',
                        options: {
                            importLoaders: 2,  // postcss-loader, sass-loader
                            esModule: false,   // css-loader v3->v4 upgrade broke this
                        },
                    },
                    {
                        loader: 'postcss-loader',
                        options: {
                            ident: 'postcss',
                            plugins: [
                                require ('autoprefixer') ({}),
                            ],
                        },
                    },
                    'sass-loader',
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
    ],
    devServer: {
        host: '127.0.6.1',
        port: 8080,
        contentBase: './build',
        public: 'ntg.fritz.box:8080',
        headers: {
            'Access-Control-Allow-Origin'      : '*',
            'Access-Control-Allow-Credentials' : 'true',
            'Content-Security-Policy'          : 'worker-src blob:',
        },
    },
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
            path.resolve (__dirname, 'src/components'),
            path.resolve (__dirname, 'src/css'),
            path.resolve (__dirname, 'src/js'),
            'node_modules',
        ],
        mainFields: ['module', 'main'],
        alias: {
            /* See: https://webpack.js.org/configuration/resolve/#resolve-alias */
            'bootstrap-custom' : path.resolve (
                __dirname, 'src/css/bootstrap-custom.scss'
            ),
        },
    },
};

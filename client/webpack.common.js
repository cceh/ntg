const path            = require ('path');
const VueLoaderPlugin = require ('vue-loader/lib/plugin'); // loads vue single-file components

module.exports = {
    entry : {
        app : 'app.js', // entrypoint in app.bundle.js
    },
    output : {
        filename : 'js/[name].bundle.js',         // make 3 bundles
        path : path.resolve (__dirname, 'build'), // in the build directory
    },
    module : {
        rules : [
            {
                test: /\.vue$/,
                exclude: /node_modules/,
                use: [
                    'vue-loader',
                ],
            },
            {
                test : /\.js$/,
                exclude : /node_modules/,
                use : [
                    'babel-loader',
                ],
            },
            {
                test: /\.scss$/,
                use: [
                    'style-loader',
                    'css-loader',
                    'postcss-loader',
                    'sass-loader',
                ],
            },
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader',
                    'postcss-loader',
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
    resolve: {
        modules: [
            path.resolve (__dirname, 'src/components'),
            path.resolve (__dirname, 'src/css'),
            path.resolve (__dirname, 'src/js'),
            'node_modules',
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
};

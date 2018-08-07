const merge  = require ('webpack-merge');
const common = require ('./webpack.common.js');

module.exports = merge (common, {
    mode: 'development',
    devtool: 'eval-source-map',
    devServer: {
        host: '127.0.6.1',
        port: 8080,
        contentBase: './build',
        public: 'ntg.fritz.box:8080',
    },
});

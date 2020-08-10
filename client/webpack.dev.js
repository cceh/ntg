const { merge }       = require ('webpack-merge');
const common          = require ('./webpack.common.js');
// const BundleAnalyzer  = require ('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = merge (common, {
    mode: 'development',
    devtool: 'eval-source-map',
    plugins: [
        // new BundleAnalyzer (),
    ],
});

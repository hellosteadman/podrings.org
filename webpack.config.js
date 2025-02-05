const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
    entry: './assets/js/app.js',
    mode: 'production',
    output: {
        path: path.resolve(__dirname, './podrings/theme/static/js'),
        filename: 'site.js',
        devtoolModuleFilenameTemplate: '[absolute-resource-path]'
    },
    module: {
        rules: [
            {
                test: /\.scss$/,
                exclude: /\.png|jpg|jpeg|gif|svg$/,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    'sass-loader'
                ]
            },
            {
                test: /\.hbs$/,
                loader: 'handlebars-loader'
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: 'babel-loader'
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin(
            {
                filename: '../css/site.css'
            }
        )
    ],
    devtool: 'source-map'
}

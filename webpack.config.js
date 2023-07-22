const path = require('path');
const nodeExternals = require('webpack-node-externals');

module.exports = {
  entry: './app.js', // Update this to your main entry point
  target: 'node',
  output: {
    path: path.resolve(__dirname, 'dist'), // Output directory (create this folder)
    filename: 'bundle.js', // Output file name
  },
  externals: [nodeExternals()], // Do not bundle node_modules
  mode: 'production', // Use 'production' for minified output
};

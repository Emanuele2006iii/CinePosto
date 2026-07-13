const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

config.resolver.resolveRequest = (context, moduleName, platform) => {
  if (platform === 'web') {
    if (moduleName === 'react-native/Libraries/Utilities/codegenNativeComponent') {
      return {
        type: 'sourceFile',
        filePath: require.resolve('./shims/codegenNativeComponent.web.js'),
      };
    }
  }
  return context.resolveRequest(context, moduleName, platform);
};

module.exports = config;

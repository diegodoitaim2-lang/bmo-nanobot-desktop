const path = require('path');
const { execFileSync } = require('child_process');

exports.default = async function afterPack(context) {
  if (context.electronPlatformName !== 'win32') return;

  const rcedit = path.join(context.packager.projectDir, 'node_modules', 'electron-winstaller', 'vendor', 'rcedit.exe');
  const icon = path.join(context.packager.projectDir, 'build-support', 'icon.ico');
  const exe = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.exe`);

  execFileSync(rcedit, [
    exe,
    '--set-icon',
    icon,
    '--set-version-string',
    'FileDescription',
    'BMO',
    '--set-version-string',
    'ProductName',
    'BMO',
    '--set-version-string',
    'CompanyName',
    'BMO',
    '--set-version-string',
    'LegalCopyright',
    'BMO',
  ]);
};

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bmoDesktop', {
  saveFile: (options) => ipcRenderer.invoke('bmo:save-file', options),
});

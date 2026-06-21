const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('bmoDesktop', {
  saveFile: (options) => ipcRenderer.invoke('bmo:save-file', options),
  getBmoToken: () => ipcRenderer.invoke('bmo:get-token'),
});

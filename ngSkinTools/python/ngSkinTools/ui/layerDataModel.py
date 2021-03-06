from maya import cmds,mel
from ngSkinTools.layerUtils import LayerUtils
from ngSkinTools.ui.events import LayerEvents, MayaEvents
from ngSkinTools.utils import Utils
from ngSkinTools.log import LoggerFactory
from ngSkinTools.mllInterface import MllInterface
from ngSkinTools.utilities.weightsClipboard import WeightsClipboard


class LayerDataModel:
    log = LoggerFactory.getLogger("layerDataModel")

    class MirrorCacheStatus:
        def __init__(self):
            self.isValid = None
            self.message = None
            self.mirrorAxis = None
    
    
    # holds instance of singleton object
    __instance = None
    
    @staticmethod
    def getInstance():
        '''
        returns singleton instance of LayerDataModel
        '''
        if LayerDataModel.__instance is None:
            LayerDataModel.__instance = LayerDataModel()
        
        return LayerDataModel.__instance
    
    @staticmethod
    def reset():
        LayerDataModel.__instance = None
    
    def __init__(self):
        self.layerListsUI = None
        self.layerDataAvailable = None
        self.mirrorCache = self.MirrorCacheStatus()
        self.mll = MllInterface()
        self.clipboard = WeightsClipboard(self.mll)
        
        MayaEvents.undoRedoExecuted.addHandler(self.updateLayerAvailability)
        MayaEvents.nodeSelectionChanged.addHandler(self.updateLayerAvailability)
        
        self.updateLayerAvailability()
        
    def setLayerListsUI(self,ui):
        self.layerListsUI = ui
        
    def getSelectedLayer(self):
        if self.layerListsUI is None:
            return None
        return self.layerListsUI.getLayersList().getSelectedID()
    
    def updateLayerAvailability(self):
        '''
        updates interface visibility depending on availability of layer data 
        '''
        self.log.info("updating layer availability")
        

        oldValue = self.layerDataAvailable
        self.layerDataAvailable = self.mll.getLayersAvailable()
        if self.layerDataAvailable!=oldValue:
            LayerEvents.layerAvailabilityChanged.emit()
        
        self.updateMirrorCacheStatus()
            
    def updateMirrorCacheStatus(self):
        def setStatus(newStatus,message,axis=None):
            change = newStatus != self.mirrorCache.isValid or self.mirrorCache.message != message or self.mirrorCache.mirrorAxis != axis
              
            self.mirrorCache.message = message
            self.mirrorCache.isValid = newStatus
            self.mirrorCache.mirrorAxis = axis
            if change:
                self.log.info("mirror cache status changed to %s." % self.mirrorCache.message)
                LayerEvents.mirrorCacheStatusChanged.emit()        

        self.log.info("updating mirror cache status")
        if not self.layerDataAvailable:
            setStatus(False,"Layer Data is not available")
            return
        
        try:
            cacheInfo = cmds.ngSkinLayer(q=True,mirrorCacheInfo=True)
            if cacheInfo[0]=='ok':
                setStatus(True,'Mirror Data Initialized',cmds.ngSkinLayer(q=True,mirrorAxis=True))
            else:
                setStatus(False,cacheInfo[1])
        except :
            setStatus(False,'Cache check failed')
            #log.error("error: "+str(err))
        
            
    def addLayer(self,name):
        id = self.mll.createLayer(name)
        
        if id is None:
            return
        LayerEvents.layerListModified.emit()
        
        self.setCurrentLayer(id)
        
    def removeLayer(self,id):
        cmds.ngSkinLayer(rm=True,id=id)
        LayerEvents.layerListModified.emit()
        LayerEvents.currentLayerChanged.emit()
        
        
    def setCurrentLayer(self,id):
        
        cmds.ngSkinLayer(cl=id)
        LayerEvents.currentLayerChanged.emit()
        
    def getCurrentLayer(self):
        return self.mll.getCurrentLayer()
        return cmds.ngSkinLayer(q=True,cl=True)
        
    def attachLayerData(self):
        self.mll.initLayers()
        self.addLayer('Base Weights')

        
        self.updateLayerAvailability() 

        
        
    def cleanCustomNodes(self):
        '''
        removes all custom nodes from current scene
        '''
        LayerUtils.deleteCustomNodes()
        
        self.updateLayerAvailability()
        
    def getLayerName(self,id):
        return mel.eval('ngSkinLayer -id %d -q -name' % id)       
    
    def setLayerName(self,id,name):
        cmds.ngSkinLayer(e=True,id=id,name=name)
        LayerEvents.nameChanged.emit()   

    def getLayerOpacity(self,id):
        return mel.eval('ngSkinLayer -id %d -q -opacity' % id)

    def getLayerEnabled(self,id):
        return mel.eval('ngSkinLayer -id %d -q -enabled' % id)
    
    def setLayerEnabled(self,id,enabled):
        cmds.ngSkinLayer(e=True,id=id,enabled=1 if enabled else 0)
        
    def toggleLayerEnabled(self,id):
        self.setLayerEnabled(id, not self.getLayerEnabled(id))
            
    def getLayersCandidateFromSelection(self):
        '''
        for given selection, returns mesh and skin cluster node names where skinLayer data
        is (or can be) attached. 
        '''
        try:
            return cmds.ngSkinLayer(q=True,ldt=True)
        except:
            return []
    
    def getLayersAvailable(self):
        self.updateLayerAvailability()
        return self.layerDataAvailable
        

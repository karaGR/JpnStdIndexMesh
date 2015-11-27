# -*- coding: utf-8 -*-
from PyQt4.Qt import QAction
import os
import sys

from mesh_canvas import mesh_canvas

sys.path.append(os.path.expanduser('~/.qgis2/python/plugins/TileLayerPlugin'))
from TileLayerPlugin.tiles import BoundingBox

class main:
    
    def __init__(self,iface):
        self.iface = iface
            
    def initGui(self):
        self.action = QAction(u"インデックスマップの表示",self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(u"&標準地域メッシュツール",self.action)
            
    def unload(self):
        
        self.iface.removePluginMenu(u"&標準地域メッシュツール", self.action)
            
    def run(self):
        tile_name = u"標準地図"
        tile_credit = u"国土地理院"       
        tile_url = u"http://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"
        tile_zmin = 1
        tile_zmax = 18
        tile_bbox = None 
#         tile_bbox = BoundingBox(-180, -85.05, 180, 85.05)
        self.canvas = mesh_canvas(self.iface,tile_name,tile_credit,tile_url,tile_zmin,tile_zmax,tile_bbox)
        self.canvas.show()
        
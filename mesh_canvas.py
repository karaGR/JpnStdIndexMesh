# -*- coding: utf-8 -*-

from qgis.core import QgsMapLayerRegistry,QgsVectorLayer
from qgis.core import QgsField,QgsFeature
from qgis.core import QgsPoint,QgsGeometry
from qgis.core import QgsCoordinateReferenceSystem,QgsCoordinateTransform

from qgis._gui import QgsMapCanvas,QgsMapCanvasLayer
from qgis.utils import plugins

import os
import sys

sys.path.append(os.path.expanduser('~/.qgis2/python/plugins/TileLayerPlugin'))
from tilelayerplugin import TileLayerPlugin
from TileLayerPlugin.tiles import BoundingBox, TileLayerDefinition
from TileLayerPlugin.tilelayer import TileLayer, TileLayerType

from PyQt4 import QtCore, QtGui
import math

class mesh_canvas(QgsMapCanvas):
    
    def __init__(self,iface,tile_name,tile_credit,tile_url,tile_zmin,tile_zmax,tile_bbox):
    
        QgsMapCanvas.__init__(self)
        self.iface = iface
        self.setWheelAction(QgsMapCanvas.WheelZoom,1)
        self.setDestinationCrs(self.iface.mapCanvas().mapSettings().destinationCrs())
        self.setCrsTransformEnabled(True)
        
        self.iface.mapCanvas().destinationCrsChanged.connect(self.onCrsChanged)
        self.iface.mapCanvas().extentsChanged.connect(self.onExtentsChanged)
        self.iface.mapCanvas().scaleChanged.connect(self.onScaleChanged)
        
        layerdef = TileLayerDefinition(tile_name,
                                       tile_credit,
                                       tile_url,
                                       zmin=tile_zmin,
                                       zmax=tile_zmax,
                                       bbox=tile_bbox)
        creditVisibility=True

        plugin = plugins.get("TileLayerPlugin")
        self.chirin_layer = TileLayer(plugin,layerdef, creditVisibility)
        QgsMapLayerRegistry.instance().addMapLayer(self.chirin_layer,False)
        
        self.meshPolyLayer = QgsVectorLayer("polygon?crs=postgis:4612",u"地域メッシュインデックス","memory")
        
        renderer = self.meshPolyLayer.rendererV2()
        renderer.symbols()[0].symbolLayers()[0].setFillColor(QtGui.QColor(0,0,0,0))
        renderer.symbols()[0].symbolLayers()[0].setBorderWidth(0.1)
        
        self.meshPolyLayer.label().setLabelField(0,0)
        
        self.meshPolyLayer.startEditing()
        self.meshPolyLayer.addAttribute(QgsField("meshC",QtCore.QVariant.String))
        self.meshPolyLayer.commitChanges()
        
        QgsMapLayerRegistry.instance().addMapLayer(self.meshPolyLayer,False)
        
        main_crs =  self.iface.mapCanvas().mapSettings().destinationCrs()
        self.Trs_laln = QgsCoordinateTransform(main_crs,QgsCoordinateReferenceSystem(4612))
        self.redraw_mesh()
             
        layers = []
        layers.append(QgsMapCanvasLayer(self.meshPolyLayer))
        layers.append(QgsMapCanvasLayer(self.chirin_layer))
        
        self.setLayerSet(layers)
        self.setExtent( self.iface.mapCanvas().extent() )
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.resize(self.iface.mapCanvas().size()/2)
        
    def onCrsChanged(self):
        main_crs =  self.iface.mapCanvas().mapSettings().destinationCrs()
        self.setDestinationCrs(main_crs)

        
    def onExtentsChanged(self):
        self.setExtent( self.iface.mapCanvas().extent() )    
        self.redraw_mesh()
        self.iface.actionPan().trigger()
        self.refresh()
        
    def onScaleChanged(self):
        self.resize(self.iface.mapCanvas().size()/2)
        
    def PPopend(self):
        self.iface.mapCanvas().extentsChanged.disconnect()
        self.iface.mapCanvas().scaleChanged.disconnect()
        
    def res_mesh_index(self,latitude,longitude):
        x1d = math.floor(longitude - 100)
        x2d = math.floor((longitude - x1d - 100 ) * 8 )
        x3d = math.floor((longitude - x1d - 100 - x2d/8.0 )*80 )
        y1d = math.floor(latitude*1.5)
        y2d = math.floor((latitude*1.5 - y1d ) * 8 )
        y3d = math.floor((latitude*1.5 - y1d - y2d/8.0 )*80 ) 
        
        return (x1d,x2d,x3d,y1d,y2d,y3d)
        
    def res_extent_mesh(self):
        main_crs =  self.iface.mapCanvas().mapSettings().destinationCrs()
        self.Trs_laln.setSourceCrs(main_crs)
        
        my_rect = self.iface.mapCanvas().extent()        
        laln_rect = self.Trs_laln.transform(my_rect)        
        
        x_min = laln_rect.xMinimum()
        x_max = laln_rect.xMaximum()
        y_min = laln_rect.yMinimum()
        y_max = laln_rect.yMaximum()

        Lx1d,Lx2d,Lx3d,Ly1d,Ly2d,Ly3d = self.res_mesh_index(y_min, x_min)
        Rx1d,Rx2d,Rx3d,Uy1d,Uy2d,Uy3d = self.res_mesh_index(y_max, x_max)
        x_range = x_max - x_min
        y_range = y_max = y_min
        
        return {"Lx1d":Lx1d,"Lx2d":Lx2d,"Lx3d":Lx3d,
                "Rx1d":Rx1d,"Rx2d":Rx2d,"Rx3d":Rx3d,
                "Ly1d":Ly1d,"Ly2d":Ly2d,"Ly3d":Ly3d,
                "Uy1d":Uy1d,"Uy2d":Uy2d,"Uy3d":Uy3d,
                "xRange":x_range,"yRange":y_range}
        
    def draw_m1d(self):
        x = self.e_mesh["Lx1d"] -1
        while x <= self.e_mesh["Rx1d"] + 1:
                 
            y = self.e_mesh["Ly1d"] 
            while y <= self.e_mesh["Uy1d"]:
                
                f = QgsFeature(self.meshPolyLayer.pendingFields())
                f.setGeometry(QgsGeometry.fromPolygon(
                        [[QgsPoint(x+100,y/1.5),QgsPoint(x+100,(y+1)/1.5),
                        QgsPoint(x+101,(y+1)/1.5),QgsPoint(x+101,y/1.5)]]))
                
                m1d_str = str(int(y)) + str(int(x))
            
                f.setAttribute("meshC",m1d_str)
                self.meshPolyLayer.addFeature(f)
                y += 1
        
            x += 1
            
    def draw_m2d(self):
        x = self.e_mesh["Lx1d"] + self.e_mesh["Lx2d"] / 8.0 - 1 / 8.0      
        while x <= self.e_mesh["Rx1d"] + self.e_mesh["Rx2d"] / 8.0 + 1 / 8.0:
            
            x1d = math.floor(x)
            x2d = math.floor((x-x1d)*8)
                 
            y = self.e_mesh["Ly1d"] + self.e_mesh["Ly2d"] / 8.0 - 1 / 8.0 
            while y <= self.e_mesh["Uy1d"] + self.e_mesh["Uy2d"] + 1 / 8.0:
                
                y1d = math.floor(y)
                y2d = math.floor((y-y1d)*8)
                
                f = QgsFeature(self.meshPolyLayer.pendingFields())
                f.setGeometry(QgsGeometry.fromPolygon(
                        [[QgsPoint(x+100,y/1.5),QgsPoint(x+100,(y+1/8.0)/1.5),
                        QgsPoint(x+100+1/8.0,(y+1/8.0)/1.5),QgsPoint(x+100+1/8.0,y/1.5)]]))
                
                m1d_str = str(int(y1d)) + str(int(x1d))
                m2d_str = str(int(y2d)) + str(int(x2d))
                mesh_str = m1d_str + m2d_str
                    
                f.setAttribute("meshC",mesh_str)                                
                self.meshPolyLayer.addFeature(f)
                
                y += 1/8.0
                
            x += 1/8.0
  
    def draw_m3d(self):
        x = self.e_mesh["Lx1d"] + self.e_mesh["Lx2d"] / 8.0 + self.e_mesh["Lx3d"] / 80.0 - 1 / 80.0
        while x <= self.e_mesh["Rx1d"] + self.e_mesh["Rx2d"] / 8.0 + self.e_mesh["Rx3d"] / 80.0 + 1 / 80.0:
            
            x1d = math.floor(x)
            x2d = math.floor((x-x1d)*8)
            x3d = math.floor((x-x1d-x2d/8.0)*80)
                 
            y = self.e_mesh["Ly1d"] + self.e_mesh["Ly2d"] / 8.0 + self.e_mesh["Ly3d"] / 80.0 - 1 / 80.0
            while y <= self.e_mesh["Uy1d"] + self.e_mesh["Uy2d"] / 8.0 + self.e_mesh["Uy3d"] / 80.0 + 1 / 80.0:
                
                y1d = math.floor(y)
                y2d = math.floor((y-y1d)*8)
                y3d = math.floor((y-y1d-y2d/8.0)*80)
                
                f = QgsFeature(self.meshPolyLayer.pendingFields())
                f.setGeometry(QgsGeometry.fromPolygon(
                        [[QgsPoint(x+100,y/1.5),QgsPoint(x+100,(y+1/80.0)/1.5),
                        QgsPoint(x+100+1/80.0,(y+1/80.0)/1.5),QgsPoint(x+100+1/80.0,y/1.5)]]))
                
                m1d_str = str(int(y1d)) + str(int(x1d))
                m2d_str = str(int(y2d)) + str(int(x2d))
                m3d_str = str(int(y3d)) + str(int(x3d))
                mesh_str = m1d_str + m2d_str + m3d_str
                    
                f.setAttribute("meshC",mesh_str)                                
                self.meshPolyLayer.addFeature(f)
                
                y += 1/80.0
                
            x += 1/80.0              
    
                
                
    def draw_m5x(self):
        x = self.e_mesh["Lx1d"] - 1
        while x <= self.e_mesh["Rx1d"]+1:
            
            x1d = math.floor(x)
            x2d = math.floor((x-x1d)*8)
            x5x = math.floor((x-x1d-x2d/8.0)*16)
                 
            y = self.e_mesh["Ly1d"] - 1 
            while y <= self.e_mesh["Uy1d"]+1:
                
                y1d = math.floor(y)
                y2d = math.floor((y-y1d)*8)
                y5x = math.floor((y-y1d-y2d/8.0)*16)
                
                f = QgsFeature(self.meshPolyLayer.pendingFields())
                f.setGeometry(QgsGeometry.fromPolygon(
                        [[QgsPoint(x+100,y/1.5),QgsPoint(x+100,(y+1/16.0)/1.5),
                        QgsPoint(x+100+1/16.0,(y+1/16.0)/1.5),QgsPoint(x+100+1/16.0,y/1.5)]]))
                
                m1d_str = str(int(y1d)) + str(int(x1d))
                m2d_str = str(int(y2d)) + str(int(x2d))
                m5x_str = str(int(x5x+y5x*2+1))
                mesh_str = m1d_str + "-" + m2d_str + "-" + m5x_str
                    
                f.setAttribute("meshC",mesh_str)                                
                self.meshPolyLayer.addFeature(f)
                
                y += 1/16.0
                
            x += 1/16.0
            
        
    def redraw_mesh(self):
        
        self.e_mesh = self.res_extent_mesh()
        if self.e_mesh["xRange"] < 50:
        
            self.meshPolyLayer.startEditing()
            self.meshPolyLayer.selectAll()
            self.meshPolyLayer.deleteSelectedFeatures()

            if self.e_mesh["xRange"]  > 2.0:
                self.draw_m1d()
            elif self.e_mesh["xRange"] > 1.0/8.0:
                self.draw_m2d()
            else:
                self.draw_m3d()
        
            self.meshPolyLayer.commitChanges()
            
            self.meshPolyLayer.enableLabels(self.e_mesh["xRange"] <= 8.0)
        
    def closeEvent(self,event):
        QgsMapLayerRegistry.instance().removeMapLayers(
            [ self.meshPolyLayer.id(), self.chirin_layer.id() ])
        self.iface.mapCanvas().destinationCrsChanged.disconnect()
        self.iface.mapCanvas().extentsChanged.disconnect()
        self.iface.mapCanvas().scaleChanged.disconnect()
    
    
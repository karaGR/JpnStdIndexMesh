# -*- coding: utf-8 -*-

#===================================
#標準地域メッシュコード表示プラグイン
#
#===================================

def classFactory(iface):
    from .main import main
    return main(iface)
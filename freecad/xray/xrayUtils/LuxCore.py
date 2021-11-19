#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2011, 2016 Jose Luis Cercos Pita <jlcercos@gmail.com>   *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

import os
import sys
import requests
import platform
import site
from importlib import reload
import OpenEXR, Imath
import numpy as np
import FreeCAD as App


LUXCORE_LATEST = "https://github.com/LuxCoreRender/LuxCore/releases/download/latest/"
URIS = {
    "linux" : LUXCORE_LATEST + "luxcorerender-latest-linux64.tar.bz2",
    "darwin" : LUXCORE_LATEST + "luxcorerender-latest-mac64.dmg",
    "windows" : LUXCORE_LATEST + "luxcorerender-latest-win64.zip",
}
CURRENT_SESSION = None


def get(folder=None):
    """Returns the luxcore library if possible, None if it is not available

    Keyword arguments:
    folder -- The folder where it is supposed we are finding it. If None,
              App.getUserAppDataDir() will be used

    Returns:
    The luxcore library, None if there is no such library
    """
    folder = os.path.join(folder or App.getUserAppDataDir(), 'LuxCore')
    if not os.path.isdir(folder):
        return None
    if folder not in sys.path:
        sys.path.append(folder)
        reload(site)
    try:
        import pyluxcore
        return pyluxcore
    except ImportError:
        print("ImportError", sys.path)
        pass
    return None


def download(folder=None):
    """Download the latest available LuxCore

    Keyword arguments:
    folder -- The folder where it will be downloaded. If None,
              App.getUserAppDataDir() will be used

    Returns:
    The luxcore library, None if there is no such library
    """
    pyluxcore = get(folder)
    if pyluxcore is not None:
        return pyluxcore

    folder = folder or App.getUserAppDataDir()
    uri = URIS[platform.system().lower()]
    fname = os.path.basename(uri)
    _, ext = os.path.splitext(fname)
    App.Console.PrintMessage("Downloading '{}' in '{}'...\n".format(uri, folder))
    data = requests.get(uri, allow_redirects=True)
    with open(os.path.join(folder, fname), 'wb') as f:
        f.write(data.content)

    if ext == ".bz2":
        import tarfile
        tf = tarfile.open(os.path.join(folder, fname), 'r:bz2')
        tf.extractall(path=folder)
    elif ext == ".zip":
        import zipfile
        tf = zipfile.ZipFile(os.path.join(folder, fname))
        tf.extractall(path=folder)
    elif ext in [".7z", ".7zip", ".dmg"]:
        import py7zr 
        tf = py7zr.SevenZipFile(os.path.join(folder, fname), mode='r')
        tf.extractall(path=folder)

    return get(folder)


def run_sim(folder, cfg="render.cfg", scn="scene.scn", pyluxcore=None,
            refresh_interval=2500):
    pyluxcore = pyluxcore or download()
    cmd_props = pyluxcore.Properties()
    cmd_props.Set(pyluxcore.Property("scene.file", scn))
    cmd_props.Set(pyluxcore.Property("screen.tool.type", "IMAGE_VIEW"))

    os.chdir(folder)

    cfg_props = pyluxcore.Properties(cfg)
    cfg_props.Set(cmd_props);
    config = pyluxcore.RenderConfig(cfg_props)

    config.Parse(pyluxcore.Properties().Set(
        pyluxcore.Property("screen.refresh.interval", refresh_interval)))

    session = pyluxcore.RenderSession(config, None, None)
    session.Start()

    global CURRENT_SESSION
    CURRENT_SESSION = session

    return session


def get_imgs(folder, session=CURRENT_SESSION):
    if session is None:
        return None

    session.GetFilm().Save()

    pt = Imath.PixelType(Imath.PixelType.FLOAT)
    exr = OpenEXR.InputFile(os.path.join(folder, "oidn.exr"))
    dw = exr.header()['dataWindow']
    size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
    imgs = []
    for channel in ('R', 'G', 'B'):
        img = np.frombuffer(exr.channel(channel, pt), dtype=np.float32)
        img.shape = (size[1], size[0])
        imgs.append(img)
    return imgs

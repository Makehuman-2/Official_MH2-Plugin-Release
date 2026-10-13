"""
    License information: data/licenses/makehuman_license.txt
    Author: black-punkduck

    Classes:
    * Light
"""
from PySide6.QtGui import QVector3D, QVector4D

class Light():
    """
    can be used to manipulate light in scene, used for up to 3 lights
    """

    def __init__(self, shaders, glob):
        self.glob = glob
        self.shaderInit = glob.shaderInit
        self.shaders = shaders
        self.phong = shaders.getShader("phong")
        self.pbr = shaders.getShader("pbr")
        self.toon = shaders.getShader("toon")
        #
        # volume of scene in units
        #
        self.min_coords = [-25.0, -25.0, -25.0 ]
        self.max_coords = [25.0, 25.0, 25.0 ]

        self.glclearcolor = QVector4D()
        self.ambientLight = QVector4D()
        self.lightWeight = QVector3D()
        self.blinn = False
        self.skybox = True
        self.skyboxname = None

        self.lights = [ 
                { "pos": QVector3D(), "vol": QVector3D(), "int": 0.0, "type": 0 }, 
                { "pos": QVector3D(), "vol": QVector3D(), "int": 0.0, "type": 0 },
                { "pos": QVector3D(), "vol": QVector3D(), "int": 0.0, "type": 0 },
                ]
        self.fromGlobal(False)

    def numLights(self):
        return len(self.lights)

    def listTo3D(self, v, elems):
        v.setX(elems[0])
        v.setY(elems[1])
        v.setZ(elems[2])

    def listTo4D(self, v, elems):
        v.setX(elems[0])
        v.setY(elems[1])
        v.setZ(elems[2])
        v.setW(elems[3])

    def q3ToList(self, v):
        return (v.x(), v.y(), v.z())

    def q4ToList(self, v):
        return (v.x(), v.y(), v.z(), v.w())

    def fromGlobal(self, load_json):
        if load_json:
            self.shaderInit = self.glob.readShaderInitJSON()
        self.blinn = self.shaderInit["blinn"]
        self.skybox = self.shaderInit["skybox"]
        self.skyboxname = self.shaderInit["skyboxname"]
        self.listTo4D(self.glclearcolor, self.shaderInit["glclearcolor"])
        self.listTo4D(self.ambientLight, self.shaderInit["ambientcolor"])
        self.lightWeight.setY(self.shaderInit["specularfocus"])
        for i, d in enumerate(self.lights):
            s = self.shaderInit["lamps"][i]
            self.listTo3D(d["pos"], s["position"])
            self.listTo3D(d["vol"], s["color"][:3])     # color + intensity are in one array in json
            d["int"] = s["color"][3]
            d["type"] = s["type"]
        self.setShader()

    def toGlobal(self):
        self.shaderInit["blinn"] = self.blinn
        self.shaderInit["glclearcolor"] = self.q4ToList(self.glclearcolor)
        self.shaderInit["ambientcolor"] = self.q4ToList(self.ambientLight)
        self.shaderInit["specularfocus"] =  self.lightWeight.y()
        self.shaderInit["skyboxname"] = self.skyboxname
        for i, s in enumerate(self.lights):
            d = self.shaderInit["lamps"][i]
            d["position"] = self.q3ToList(s["pos"])

            d["color"]    = list(self.q3ToList(s["vol"]))  # recombine array
            d["color"].append(s["int"])

            d["type"] = s["type"]

    def setShader(self):
        for shader in [self.phong, self.pbr, self.toon]:
            self.shaders.bindShader(shader)
            for i, elem in enumerate(self.lights):
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "position", elem["pos"])
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "color", elem["vol"])
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "intensity", elem["int"])
                self.shaders.setShaderArrayStruct(shader, "pointLights", i, "type", elem["type"])
            self.shaders.setShaderUniform(shader, "ambientLight", self.ambientLight)
        
        # next ones are only for phong
        #
        self.shaders.bindShader(self.phong)
        self.shaders.setShaderUniform(self.phong, "blinn", self.blinn)
        self.shaders.setShaderUniform(self.phong, "lightWeight", self.lightWeight)

    def useBlinn(self, value):
        if value != self.blinn:
            self.blinn = value
            self.setShader()

    def useSkyBox(self, value):
        self.skybox = value

    def getAmbientLuminance(self):
        return float(self.ambientLight.w())

    def setAmbientLuminance(self, value):
        self.ambientLight.setW(value)
        self.setShader()

    def setSpecularLuminance(self, value):
        self.lightWeight.setX(value)
        self.setShader()

    def setSpecularFocus(self, value):
        self.lightWeight.setY(value)
        self.setShader()

    def getClearColor(self):
        return [round(self.glclearcolor.x(), 4), round(self.glclearcolor.y(), 4), round(self.glclearcolor.z(), 4)]

    def setClearColor(self, value):
        self.glclearcolor.setX(value.redF())
        self.glclearcolor.setY(value.greenF())
        self.glclearcolor.setZ(value.blueF())
        self.glclearcolor.setW(1.0)

    def getAmbientColor(self):
        return [round(self.ambientLight.x(), 4), round(self.ambientLight.y(), 4), round(self.ambientLight.z(), 4)]

    def setAmbientColor(self, value):
        self.ambientLight.setX(value.redF())
        self.ambientLight.setY(value.greenF())
        self.ambientLight.setZ(value.blueF())
        self.setShader()

    def setHPos(self, num, y):
        m =  self.lights[num]["pos"]
        m.setY(y)
        self.setShader()

    def setLPos(self, num, x, z):
        m =  self.lights[num]["pos"]
        m.setX(x)
        m.setZ(z)
        self.setShader()

    def getLPos(self, num):
        m =  self.lights[num]["pos"]
        return [round(m.x(), 4), round(m.y(), 4), round(m.z(), 4)]

    def setType(self, num, ltype):
        self.lights[num]["type"] = ltype
        self.setShader()

    def getType(self, num):
        return self.lights[num]["type"]

    def setLLuminance(self, num, value):
        self.lights[num]["int"] = value
        self.setShader()

    def getLLuminance(self, num):
        return float(self.lights[num]["int"])

    def setLColor(self, num, value):
        m =  self.lights[num]["vol"]
        m.setX(value.redF())
        m.setY(value.greenF())
        m.setZ(value.blueF())
        self.setShader()

    def getLColor(self, num):
        m =  self.lights[num]["vol"]
        return [round(m.x(), 4), round(m.y(), 4), round(m.z(), 4)]

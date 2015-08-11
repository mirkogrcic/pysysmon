#!/usr/bin/python3

__author__ = 'mirko'

import sys, os, ctypes as ct
from time import clock, sleep
from os import path

import OpenGL.GL as gl
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ctypes import *

try:import numpy as np
except:np = None


def setMatrix(l,r,b,t):
    """

    :param l: left
    :param r: right
    :param b: bottom
    :param t: top
    :return:
    """
    matrix = [0] * 16

    matrix[0] = 2/(r-l)
    matrix[5] = 2/(t-b)
    matrix[10] = -1
    matrix[12] = -(r+l)/(r-l)
    matrix[13] = -(t+b)/(t-b)
    matrix[15] = 1

    glLoadMatrixf(matrix)

def getVBOData(coords):
    """

    :param coords:
    :return: data
    """
    try:
        # faster 3x,less memory 3x
        data = np.array(coords, np.float32)
        return data
    except:
        data = (c_float*len(coords))(*coords)
        return data

def getShaderProgram(vertex, fragment):
    """

    :param vertex: vertex source
    :param fragment: fragment source
    :return: glProgramObject, vertexShaderObject, fragmentShaderObject
    """
    gls_v = glCreateShader(GL_VERTEX_SHADER)
    gls_f = glCreateShader(GL_FRAGMENT_SHADER)

    glShaderSource(gls_v, [vertex])
    glShaderSource(gls_f, [fragment])

    # region Compile
    glCompileShader(gls_v)
    error = glGetShaderInfoLog(gls_v)
    if error:
        print(error.decode())
        raise Exception("Error compiling vertex shader")

    glCompileShader(gls_f)
    error = glGetShaderInfoLog(gls_f)
    if error:
        print(error.decode())
        raise Exception("Error compiling fragment shader")
    # endregion

    glp = glCreateProgram()
    glAttachShader(glp, gls_v)
    glAttachShader(glp, gls_f)

    glLinkProgram(glp)
    error = glGetProgramInfoLog(glp)
    if error:
        print(error.decode())
        raise Exception("Error linking program")
    return glp, gls_v, gls_f

def getShaderVariableLoc(program, varname):
    if isinstance(varname, str):
        varname = varname.encode()
    loc = glGetUniformLocation(program, varname)
    if loc != -1:
        print("loc", loc)
        return loc
    else:
        raise Exception("Shader variable not found", program=program, varname=varname)


keys = {}
def getKey(key):
    return keys.get(key, False)

class Item():
    __slots__ = ("value", "time") # increases performance
    def __init__(self, value, time):
        """

        :param value:
        :param time:
        :return:
        """
        self.value = value
        self.time = time

    def __repr__(self):
        return str(self.value)

class Section():
    __slots__ = ("name", "values", "line_color", "line_fill_color", "min", "max", "cache") # increases performance
    def __init__(self,name,line_color=None, line_fill_color=None, values=None, min=0, max=100):
        """

        :param line_color:
        :param line_fill_color:
        :param values:
        :param min: scaling min, error if smaller than this
        :param max: scaling max, error if bigger than this
        :return:
        """
        self.name = name
        # list is mutable so if I set it as default
        # it has the same address in every new section
        if values is None:
            values = []
        self.values = values
        self.line_color = line_color
        self.line_fill_color = line_fill_color
        self.min = min
        self.max = max
        self.cache = {
            "vbo_l": glGenBuffers(1),
        }

    def __del__(self):
        glDeleteBuffers([self.cache["vbo_l"]])

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()
        raise exc_type(exc_val, traceback=exc_tb)

class Histograph():
    #__slots__ = []
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.borderWidth = 1
        self.itemWidth = 3
        self.sections = [] # needed for order
        self.sections_d = {} # needed for speed
        self.drawCount = 999999

        # sizeof(float) * vertexPerItem * len([x,y])
        # 4 * 2 * 2 = 16
        self.convItemByte = 16
        self.convItemCoord = 4
        self.convItemVert = 2


        self.emptyItems = 32 # resize VBO that can hold 32 new items
        self.replaceOldItems = True

        # if treplaceOldItems: start replacing after count goes above this
        self.minItemCount = 30

        self.cache = {
            #TODO :vao: use this for drawing sections, must have updates after adding/removing sections
            "vao": None,
            "vbo_border": None,

            "shaderProgram":None,
            "shaderVarFill":None,
            "shaderVarSkip":None,

            "item_index": 0,
            "vertex_index": 0,
            "line_index":0,

            "vbo_inslen":0,

            "scrollx":0,
            "motion_last_x":0,
        }

    def init(self):
        pass
        #self.cache["vao"] = glGenVertexArrays(1) # init glut and window if exception

        # region Border Lines
        data = getVBOData([
            -1,-1,
            1,-1,
            1,1,
            -1,1
        ])
        self.cache["vbo_border"] = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.cache["vbo_border"])
        glBufferData(GL_ARRAY_BUFFER, data, GL_STATIC_DRAW)
        # endregion

        # region Vertex Shader, x increment
        path = os.path.dirname(__file__)
        path = os.path.join(path, "shaders")

        with open(os.path.join(path, "vertex.glsl")) as f:
            vertex = f.read()
        with open(os.path.join(path, "fragment.glsl")) as f:
            fragment = f.read()

        program = getShaderProgram(vertex, fragment)[0]
        self.cache["shaderProgram"] = program

        self.cache["shaderVarFill"] = getShaderVariableLoc(program, b"fill")
        self.cache["shaderVarSkip"] = getShaderVariableLoc(program, b"skip")

        # endregion
        pass


    # region Drawing
    def draw(self):
        x,y = self.x, self.y
        w,h = self.width, self.height
        b = self.borderWidth
        # default matrix l,r,b,t = -1,1,-1,1

        glClearColor(.8,.8,.8,0)

        glEnableClientState(GL_VERTEX_ARRAY)

        # region Draw border
        self._drawBorder()
        # endregion


        if w <= b or h <= b:
            return
        glViewport(x+b, y+b, w-b*2, h-b*2)
        glPushMatrix()

        if getKey("p"):
            keys["p"] = False
            self.cache["item_index"] += 1

        if getKey("m"):
            keys["m"] = False
            self.cache["item_index"] -= 1

        glScalef(self.itemWidth,1,1) # scale x for item distances

        if self.cache["scrollx"]:
            glTranslatef(self.cache["scrollx"] * 2 / self.itemWidth * (1/w),0,0) # scroll alignment
        else:
            glTranslatef(self.cache["item_index"] * (1/w) * 2,0,0) # new item alignment

        glUseProgram(self.cache["shaderProgram"])
        glUniform1i(self.cache["shaderVarSkip"], self.cache["vbo_inslen"])
        for section in self.sections:
            assert isinstance(section, Section)
            # Fill
            if not getKey("1"):
                glUniform1f(self.cache["shaderVarFill"], True)
                glColor(*section.line_fill_color)
                glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
                glVertexPointer(2, GL_FLOAT, 0, None)

                glPushMatrix()
                glScalef(-2/w, 2*(h-1)/h, 1)
                glTranslatef(-w/60, -1/2, 1)
                glDrawArrays(GL_QUAD_STRIP, self.cache["vbo_inslen"]*2, len(section.values)*2)
                glPopMatrix()

            # Lines
            if not getKey("2"):
                glUniform1f(self.cache["shaderVarFill"], False)
                glColor(*section.line_color)
                glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
                glVertexPointer(2, GL_FLOAT, sizeof(c_float)*4, None)

                glPushMatrix()
                glScalef(-2/w, 2*(h-1)/h, 1)
                glTranslatef(-w/60, -1/2, 1)
                glDrawArrays(GL_LINE_STRIP, self.cache["vbo_inslen"], len(section.values))
                glPopMatrix()


        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()

    def _drawBorder(self):
        glUseProgram(0)
        borderWidth = self.borderWidth
        if borderWidth > 1:
            borderWidth *= 2 # lines do not connect right, so I double the width and apply no glTranslate
        glLineWidth(borderWidth)
        glColor3f(0,0,0)
        x,y = self.x, self.y
        w,h = self.width, self.height


        glViewport(x,y, w,h)
        glBindBuffer(GL_ARRAY_BUFFER, self.cache["vbo_border"])
        glVertexPointer(2, GL_FLOAT, 0, None)

        glPushMatrix()
        glScalef(1*(w-0.5)/w, 1*(h-0.5)/h,1) # scales both ways l/r, b/t so need half of one
        glDrawArrays(GL_LINE_LOOP, 0, 4)
        glPopMatrix()

        glLineWidth(1)

    # endregion

    def addSection(self, section:Section):
        self.sections.append(section)
        self.sections_d[section.name] = section

    def insertValue(self, section:Section, item:Item):
        self.replaceOldItems = getKey("b")

        if isinstance(section, str):
            section = self.sections_d[section]
        assert isinstance(item, Item)

        self.updateVBOSize(section) # must update before append

        section.values.append(item)
        if self.replaceOldItems and len(section.values) > self.minItemCount:
            section.values.pop(0)

        y = (item.value-section.min)/(section.max-section.min)
        coords = [1,y,0,0]

        data = getVBOData(coords)


        glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
        glBufferSubData(GL_ARRAY_BUFFER, (self.cache["vbo_inslen"]-1)*self.convItemByte, data)

        self.cache["vbo_inslen"] -= 1


        glutPostRedisplay()


    def update(self):
        """
        Call if you changed any of the folowing attributes
        sections, section.values,
        :return:
        """
        for section in self.sections:
            self.updateSection(section)

    def updateSection(self, section:Section):
        coords = []
        # region Generating coordinates
        for item in reversed(section.values):
            assert isinstance(item, Item)

            #calc y
            y = (item.value-section.min)/(section.max-section.min)

            # line_strip & quad_strip
            # can decrease from 4 to 2 using a geometry shader but it will limit gl to min 3.2
            coords.extend((1,y,0,0)) # x1 means line, x0 means quad
        # endregion

        # region Generating Vertex Buffer Object(VBO)
        data = getVBOData(coords)
        glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
        glBufferData(GL_ARRAY_BUFFER, data, GL_DYNAMIC_DRAW)
        self.cache["vbo_inslen"] = 0
        # endregion

    def updateVBOSize(self, section:Section):
        if self.cache["vbo_inslen"] >= 1:
            return
        newVBO = glGenBuffers(1)

        glBindBuffer(GL_COPY_READ_BUFFER_BINDING, section.cache["vbo_l"])
        glBindBuffer(GL_COPY_WRITE_BUFFER_BINDING, newVBO)

        emptyBytes = self.emptyItems * self.convItemByte
        itemBytes = len(section.values) * self.convItemByte # item count is being incremented

        glBufferData(GL_COPY_WRITE_BUFFER_BINDING,
                     emptyBytes + itemBytes, None, GL_DYNAMIC_DRAW)
        glCopyBufferSubData(GL_COPY_READ_BUFFER_BINDING, GL_COPY_WRITE_BUFFER_BINDING,
                            0, emptyBytes, itemBytes)
        glDeleteBuffers(1, [section.cache["vbo_l"]])

        section.cache["vbo_l"] = newVBO
        self.cache["vbo_inslen"] = self.emptyItems

    def updateMotion(self, x, press=False):
        if press:
            self.cache["motion_last_x"] = x
            return
        else:
            mlx = self.cache["motion_last_x"]
            self.cache["motion_last_x"] = x

        m = x-mlx

        scrollx = self.cache["scrollx"] + m

        sectionMax = 0
        for section in self.sections:
            sectionMax = max(sectionMax, len(section.values))

        if scrollx < 0:
            scrollx = 0

        size = self.itemWidth * sectionMax
        if scrollx:
            end =  size - self.width - self.itemWidth
            if size > self.width and scrollx > end:
                print("max")
                scrollx = end
            elif size < self.width:
                scrollx = 0

        self.cache["scrollx"] = scrollx
        glutPostRedisplay()

    # region Callbacks
    def callbackScroll(self, tillStart, tillEnd):
        """
        Will probably remove this
        If scrolling is near start or scrolling is near end:
            change the sections values and update or leave it be,
            scrolling will stop at start/end

        :param tillStart:
        :param tillEnd:
        :return: None
        """
        return

    # endregion

if __name__ == "__main__":
    print("Cannot run this module as __main_")

#!/usr/bin/python3

__author__ = 'mirko'

import sys, os, ctypes as ct
from time import clock, sleep
from os import path

import OpenGL
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
        self.insert = True #
        self.cache = {
            #TODO :vao: use this for drawing sections, must have updates after adding/removing sections
            "vao": None,
            "vbo_border": None,

            "shaderProgram":None,
            "shaderVarFill":None,

            "item_index": 0,
            "vertex_index": 0,
            "line_index":0,

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

        loc = glGetUniformLocation(program, b"fill")
        if loc != -1:
            print("loc", loc)
            self.cache["shaderVarFill"] = loc
        else:
            raise Exception("Shader variable not found")
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

        if not self.cache["scrollx"]:
            glTranslatef(self.cache["item_index"] * (1/w),0,0) # new item alignment
        if self.cache["scrollx"]:
            glTranslatef(self.cache["scrollx"] / self.itemWidth * (1/w),0,0) # scroll alignment

        glUseProgram(self.cache["shaderProgram"])
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
                glDrawArrays(GL_QUAD_STRIP, 0, len(section.values)*2)
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
                glDrawArrays(GL_LINE_STRIP, 0, len(section.values))
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

    def insertValue(self, section:Section, value:Item):
        if isinstance(section, str):
            section = self.sections_d[section]
        assert isinstance(value, Item)
        section.values.append(value)

        glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
        #


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
        for item in section.values:
            assert isinstance(item, Item)

            #calc y
            y = ((item.value-section.min)/(section.max-section.min))

            # line_strip & quad_strip
            coords.extend((1,y,0,0)) # x1 means line, x0 means quad

            # increment, I'm using glScale in draw for itemWidth
        # endregion

        # region Generating Vertex Buffer Object(VBO)
        ending = [coords[0], coords[1], coords[0], 0] # used to connect first and last because it's a strip
        data = getVBOData(coords + ending)
        glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
        glBufferData(GL_ARRAY_BUFFER, data, GL_DYNAMIC_DRAW)
        # endregion

    def updateMotion(self, x, press=False):
        if press:
            self.cache["motion_last_x"] = x
            return
        else:
            mlx = self.cache["motion_last_x"]
            self.cache["motion_last_x"] = x

        m = x-mlx
        self.cache["scrollx"] += m*2
        glutPostRedisplay()

if __name__ == "__main__":
    print("Cannot run this module as __main_")

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


_shaderProgram = None
_shaderVarFill = None
_shaderVarSkip = None


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
        return loc
    else:
        raise Exception("Shader variable not found", program=program, varname=varname)

def init():
    """
    Initalize histograph requirements(shaders)
    No need to call it, first initialized Histograph will call it
    :return:
    """
    if _shaderProgram is not None:
        return
    global _shaderProgram, _shaderVarFill, _shaderVarSkip

    path = os.path.dirname(__file__)
    path = os.path.join(path, "shaders")

    with open(os.path.join(path, "vertex.glsl")) as f:
        vertex = f.read()
    with open(os.path.join(path, "fragment.glsl")) as f:
        fragment = f.read()

    program = getShaderProgram(vertex, fragment)[0]

    _shaderProgram = program
    _shaderVarFill = getShaderVariableLoc(program, b"fill")
    _shaderVarSkip = getShaderVariableLoc(program, b"skip")


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
        glDeleteBuffers(1, [self.cache["vbo_l"]])

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

        self.fillLines = True

        # if treplaceOldItems: start replacing after count goes above this
        self.minItemCount = 30

        self.cache = {
            #TODO :vao: use this for drawing sections, must have updates after adding/removing sections
            "vao": None,
            "vbo_border": None,

            "vbo_inslen":0,

            "scrollx":0,
            "motion_last_x":None,
        }

    def init(self):

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

        init()
        pass

    #def __repr__(self):
        #return "%s %s %s %s" % self

    # region Properties
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self,v):
        if v >= 0:
            self._x = int(v)

    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, v):
        if v >= 0:
            self._y = int(v)

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, v):
        if v >= 0:
            self._width = int(v)

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, v):
        if v >= 0:
            self._height = int(v)
    # endregion


    # region Drawing
    def draw(self):
        t = clock()
        x,y = self.x, self.y
        w,h = self.width, self.height
        b = self.borderWidth
        # default matrix l,r,b,t = -1,1,-1,1

        glClearColor(.8,.8,.8,0)

        glEnableClientState(GL_VERTEX_ARRAY)


        self._drawBorder()


        if w <= b or h <= b:
            return
        glViewport(x+b, y+b, w-b*2, h-b*2)
        glPushMatrix()

        glScalef(-2/w*self.itemWidth, 2*(h-1)/h, 1) # xDistance, range(0-w)
        glTranslatef(-w/2/self.itemWidth, -1/2, 1)

        #if self.cache["scrollx"]:
        glTranslatef(-self.cache["scrollx"]/self.itemWidth ,0,0) # scroll alignment

        glUseProgram(_shaderProgram)
        glUniform1i(_shaderVarSkip, self.cache["vbo_inslen"])
        for section in self.sections:
            assert isinstance(section, Section)
            # Fill
            if self.fillLines:
                glUniform1f(_shaderVarFill, True)
                glColor(*section.line_fill_color)
                glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
                glVertexPointer(2, GL_FLOAT, 0, None)

                glPushMatrix()
                glDrawArrays(GL_QUAD_STRIP, self.cache["vbo_inslen"]*2, len(section.values)*2)
                glPopMatrix()

            # Lines
            glUniform1f(_shaderVarFill, False)
            glColor(*section.line_color)
            glBindBuffer(GL_ARRAY_BUFFER, section.cache["vbo_l"])
            glVertexPointer(2, GL_FLOAT, sizeof(c_float)*4, None)

            glPushMatrix()
            glDrawArrays(GL_LINE_STRIP, self.cache["vbo_inslen"], len(section.values))
            glPopMatrix()

        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()
        #print("draw time", (clock()-t)/1000)

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

    # region Helpers
    def _getMaxValues(self):
        n = 0
        for section in self.sections:
            n = max(n, len(section.values))
        return n

    def _isInside(self,x,y):
        if x >= self.x and x - self.x < self.width and\
            y >= self.y and y - self.y < self.height:
            return True
        return False
    # endregion

    # region Scrolling
    def scrollToEnd(self):
        self.cache["scrollx"] = (self._getMaxValues()-1) * self.itemWidth - self.width

    def scrollToStart(self):
        self.cache["scrollx"] = 0

    def scrollToLeft(self, pixels):
        self.cache["scrollx"] -= pixels
        self.updateScrollBounds()
        glutPostRedisplay()

    def scrollToRight(self, pixels):
        self.cache["scrollx"] += pixels
        self.updateScrollBounds()
        glutPostRedisplay()
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
        if self.cache["scrollx"]:
            self.cache["scrollx"] += self.itemWidth # do not move, for inspection
            self.updateScrollBounds()


        glutPostRedisplay()

    # region Updates
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

    def updateScrollBounds(self):
        scrollx = self.cache["scrollx"]

        sectionMax = self._getMaxValues()

        if scrollx < 0:
            scrollx = 0

        size = self.itemWidth * sectionMax
        if scrollx:
            end =  size - self.width - self.itemWidth
            if size > self.width and scrollx > end:
                scrollx = end
            elif size < self.width:
                scrollx = 0

        self.cache["scrollx"] = scrollx

    # endregion

    # region Keyboard and mouse input
    # Need x,y input(all inputs) origin as Left,Lower
    #   because viewport is Left,Lower based, but glut Left,Upper
    def inputKeyboard(self,key:str,x,y):
        """

        :param key:
        :param x: left
        :param y: lower
        :return:
        """
        if not self._isInside(x,y):
            return

    def inputKeyboardSpecial(self,key:int,x,y):
        """

        :param key:
        :param x: left
        :param y: lower
        :return:
        """
        if not self._isInside(x,y):
            return
        if key ==  GLUT_KEY_HOME:
            self.scrollToStart()

        elif key == GLUT_KEY_END:
            self.scrollToEnd()

        elif key == GLUT_KEY_UP:
            self.itemWidth += 1

        elif key == GLUT_KEY_DOWN:
            if self.itemWidth >= 2:
                self.itemWidth -= 1

        elif key == GLUT_KEY_LEFT:
            self.scrollToLeft(self.itemWidth)

        elif key == GLUT_KEY_RIGHT:
            self.scrollToRight(self.itemWidth)

        glutPostRedisplay()

    def inputMouse(self, key:int, pressed:bool, x,y):
        """

        :param key:
        :param released:
        :param x: left
        :param y: lower
        :return:
        """
        if self.cache["motion_last_x"] is not None and key == 0 and not pressed:
            self.cache["motion_last_x"] = None
        if not self._isInside(x,y):
            return
        if key == 0:
            if pressed:
                self.cache["motion_last_x"] = x
            else:
                self.cache["motion_last_x"] = None

    def inputWheel(self, direction:int, x,y):
        """

        :param direction:
        :param x: left
        :param y: lower
        :return:
        """
        if not self._isInside(x,y):
            return
        self.scrollToRight(direction * self.itemWidth)

    def inputMotionActive(self,x,y):
        """

        :param x: left
        :param y: lower
        :return:
        """
        # region Scrollx
        if self.cache["motion_last_x"] is not None:
            mlx = self.cache["motion_last_x"]
            self.cache["motion_last_x"] = x

            m = x-mlx
            self.scrollToRight(m)

        # endregion
        if not self._isInside(x,y):
            return



    def inputMotionPassive(self,x,y):
        if not self._isInside(x,y):
            return

    # endregion

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
    pass

if __name__ == "__main__":
    print("Cannot run this module as __main_")

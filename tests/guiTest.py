__author__ = 'mirko'

import sys, os, ctypes as ct
from time import clock, sleep

import OpenGL
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from ctypes import *

try:
    import gui.histograph as h
except:
    import histograph as h


def display():
    glClear(GL_COLOR_BUFFER_BIT)
    hg.draw()
    glutSwapBuffers()

def reshape(w,h):
    if 0:
        hg.x = 10
        hg.y = 10
        hg.width = w-20
        hg.height = h-20
    else:
        hg.width = w
        hg.height = h
    #hg.update()

def keyboard( key, x, y ):
    global scale, vert, hori, fill_it
    if key == b'\x1b':
        sys.exit( )
    elif key == b"r":
        reshape(width, height)
        glutPostRedisplay()
    elif key == b"R":
        reshape(width, height)
        hg.cache["scrollx"] = 0
        glLoadIdentity()
        glutPostRedisplay()
    elif key == b"+":
        if 1:
            glScalef(1.1, 1.1, 1)
        else:
            hg.x -= 5
            hg.y -= 5
            hg.width += 10
            hg.height += 10
        glutPostRedisplay()
    elif key == b"-":
        if 1:
            glScalef(.9, .9, 1)
        else:
            hg.x += 5
            hg.y += 5
            hg.width -= 10
            hg.height -= 10
        glutPostRedisplay()
    elif key == b"h":
        hori = not hori
        print(hori)
        reshape(width, height)
        glutPostRedisplay()
    elif key == b"v":
        vert = not vert
        print(vert)
        reshape(width, height)
        glutPostRedisplay()
    elif key == b"f":
        fill_it = not fill_it
        print(bool(fill_it))
        glutPostRedisplay()
    else:
        k = key.decode()
        h.keys[k] = not h.keys.get(k,False)
        #print(h.keys[k])
        glutPostRedisplay()
        hg.update()

def mouseKey(key, released, x,y):
    if key == 0:
        if not released:
            hg.updateMotion(x, True)


def activeMotion(x,y):
    hg.updateMotion(x)




width, height = 600,600


glutInit(sys.argv)
dmode = GLUT_DOUBLE | GLUT_RGBA
dmode |= GLUT_MULTISAMPLE
glutInitDisplayMode(dmode)
glutInitWindowPosition(10,10)
glutInitWindowSize(width,height)
glutCreateWindow(b"hello")
glutReshapeWindow(width,height)
glutReshapeFunc(reshape)
glutDisplayFunc(display)
glutKeyboardFunc(keyboard)
glutMotionFunc(activeMotion)
glutMouseFunc(mouseKey)


hg = h.Histograph(0,0,width, height)
hg.init()
hg.itemWidth = 30


section = h.Section("a", (0,.5,0), (0,1,0))
for i in [100,100,75,75,100,100, 85,80,70,80,65,87,80,80]:
    section.values.append(h.Item(i, 0))
hg.addSection(section)


section = h.Section("b", (.5,0,0), (1,0,0))
for i in [50,50,0,0,50,50, 25]:
    section.values.append(h.Item(i, 0))
hg.addSection(section)


hg.update()

glutMainLoop()
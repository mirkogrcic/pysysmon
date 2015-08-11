__author__ = 'mirko'

import sys, os, ctypes as ct, random
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

    graph.draw()

    glPushMatrix()
    glUseProgram(0)
    glColor3f(0,0,0)
    glTranslatef(-1, 0.94, 1)
    glScalef(0.0005, 0.0005, 1)
    glutStrokeString(GLUT_STROKE_ROMAN, "{x}x{y} {%}% {lval}".format(**passive).encode())
    #glutStrokeString(GLUT_STROKE_ROMAN, b"aaaaAAAAAAAAAAAAAAA\nAAA")
    glPopMatrix()

    glutSwapBuffers()

def reshape(w,h):
    if 0:
        graph.x = 10
        graph.y = 10
        graph.width = w-20
        graph.height = h-20
    else:
        graph.width = w
        graph.height = h
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
        graph.cache["scrollx"] = 0
        glLoadIdentity()
        glutPostRedisplay()
    elif key == b"+":
        if 1:
            glScalef(1.1, 1.1, 1)
        else:
            graph.x -= 5
            graph.y -= 5
            graph.width += 10
            graph.height += 10
        glutPostRedisplay()
    elif key == b"-":
        if 1:
            glScalef(.9, .9, 1)
        else:
            graph.x += 5
            graph.y += 5
            graph.width -= 10
            graph.height -= 10
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
    elif key == b"i":
        insertValue()
    else:
        k = key.decode()
        h.keys[k] = not h.keys.get(k,False)
        print(h.keys[k])
        graph.update()
        glutPostRedisplay()

def mouseKey(key, released, x,y):
    if key == 0:
        if not released:
            graph.updateMotion(x, True)



def activeMotion(x,y):
    graph.updateMotion(x)

passive = {}
for i in "x y % lval".split(" "): passive[i] = 0
def passiveMotion(x,y):
    global passive
    passive["x"] = graph.width - x
    passive["y"] = graph.height - y
    passive["%"] = round((graph.height - y)/graph.height*100, 1)
    glutPostRedisplay()


def insertValue(a=0):
    item = h.Item(random.randint(0, 100), 0)
    passive["lval"] = item.value
    graph.insertValue("a", item)

    item = h.Item(random.randint(0, 50), 0)
    #item = h.Item(0, 0)
    #graph.insertValue("b", item)

    if a:
        glutTimerFunc(1000, insertValue, 1)


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
glutPassiveMotionFunc(passiveMotion)
glutMouseFunc(mouseKey)
#glutTimerFunc(1000, insertValue, 0)

random.seed(0)

graph = h.Histograph(0,0,width, height)
graph.init()
graph.itemWidth = 30


section = h.Section("a", (0,.5,0), (0,1,0))
for i in [100,100,75,75,100,100, 85,80,70,80,65,87,80,80]:
    section.values.append(h.Item(i, 0))
graph.addSection(section)


section = h.Section("b", (.5,0,0), (1,0,0))
for i in [50,50,0,0,50,50, 25]:
    section.values.append(h.Item(i, 0))
#graph.addSection(section)


graph.update()

glutMainLoop()
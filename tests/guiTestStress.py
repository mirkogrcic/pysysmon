__author__ = 'mirko'

import sys, os, ctypes as ct, random, math
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

    for graph in graphs:
        graph.draw()

    glViewport(0,0,width,height)
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
    global width, height
    width,height = w,h
    xw = w / graphPerD
    yw = h / graphPerD

    i = 0
    for y in range(graphPerD):
        for x in range(graphPerD):
            graphs[i].x = x * xw
            graphs[i].y = y * yw
            graphs[i].width = xw
            graphs[i].height = yw
            i+= 1



def keyboard( key, x, y ):
    y = height - y
    global scale, vert, hori, fill_it
    if key == b'\x1b':
        sys.exit( )
    elif key == b"r":
        reshape(width, height)
        glutPostRedisplay()
    elif key == b"R":
        reshape(width, height)
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
        print(k, h.keys[k])
        glutPostRedisplay()

def specialKey(key, x, y):
    y = height - y
    for graph in graphs:
        graph.inputKeyboardSpecial(key,x,y)

def mouseKey(key, released, x,y):
    y = height - y
    for graph in graphs:
        if graph._isInside(x,y):
            print("in", graphs.index(graph))
        graph.inputMouse(key, not released, x, y)
        if not released:
            if key == 3: # UP
                graph.inputWheel(1,x,y)
            elif key == 4: # DOWN
                graph.inputWheel(-1,x,y)

def activeMotion(x,y):
    y = height - y
    for graph in graphs:
        graph.inputMotionActive(x,y)



passive = {}
for i in "x y % lval".split(" "): passive[i] = 0
def passiveMotion(x,y):
    global passive
    for graph in graphs:
        if not graph._isInside(x,y):
            continue
        ww = graph.x + graph.width
        wh = graph.y + graph.height
        passive["x"] = width - x
        passive["y"] = height - y
        passive["%"] = round(100-(y - graph.y)/graph.height*100, 1)
        break
    glutPostRedisplay()


def insertValue(a=0):
    if h.getKey("k"):
        item = h.Item(random.randint(0, 100), 0)
        passive["lval"] = item.value
        for graph in graphs:
            graph.insertValue("a", item)

        item = h.Item(random.randint(0, 50), 0)
        #item = h.Item(0, 0)
        #graph.insertValue("b", item)

    if a:
        glutTimerFunc(a, insertValue, a)


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
glutSpecialFunc(specialKey)
glutTimerFunc(1, insertValue, 100)

values = []
for i in [100,100,75,75,100,100, 85,80,70,80,65,87,80,80]:
    values.append(i)
for i in range(500):
    values.append(random.randint(0, 100))

graphs = []
graphPerD = 2
xw = width / graphPerD
yw = height / graphPerD

for y in range(graphPerD):
    for x in range(graphPerD):
        random.seed(0)
        graph = h.Histograph(x*xw,y*yw,xw, yw)
        graph.init()
        graph.itemWidth = 3


        section = h.Section("a", (0,.5,0), (0,1,0))
        for i in values:
            section.values.append(h.Item(i, 0))
        graph.addSection(section)


        section = h.Section("b", (.5,0,0), (1,0,0))
        for i in [50,50,0,0,50,50, 25]:
            section.values.append(h.Item(i, 0))
        #graph.addSection(section)


        graph.update()

        graphs.append(graph)
glutMainLoop()
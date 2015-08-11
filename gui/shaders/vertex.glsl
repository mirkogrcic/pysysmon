#version 330 compatibility

uniform bool fill;
uniform int skip;

void main()
{
    vec4 a = gl_Vertex;
    int skip2 = fill ? skip*2 : skip;
    if(a.x == 1)
        a.x = gl_VertexID - skip2;
    else
        a.x = gl_VertexID - skip2 - 1;
    if(fill)
        a.x /= 2;
    gl_Position = gl_ModelViewMatrix * a;
    gl_FrontColor = gl_Color;
}
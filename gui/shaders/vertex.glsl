#version 330 compatibility

uniform bool fill;

void main()
{
    vec4 a = gl_Vertex;
    if(a.x == 1)
        a.x = gl_VertexID;
    else
        a.x = gl_VertexID - 1;
    if(fill)
        a.x /= 2;
    gl_Position = gl_ModelViewMatrix * a;
    gl_FrontColor = gl_Color;
}
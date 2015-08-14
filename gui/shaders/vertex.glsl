#version 330 compatibility

uniform bool fill;
uniform int skip;
uniform int highlight;

void main()
{
    vec4 a = gl_Vertex;
    bool top = a.x==1?true:false;
    int skip2 = fill ? skip*2 : skip;
    int index = gl_VertexID - skip2;
    if(top)
        a.x = index;
    else
        a.x = index - 1;
    if(fill){
        a.x /= 2;
        index /= 2; // prepare for color
    }
    gl_Position = gl_ModelViewMatrix * a;

    if(highlight < 0)
        gl_FrontColor = gl_Color;
    else{
        if(index == highlight && top && !fill)
            gl_FrontColor = vec4(1,1,1,1) - gl_Color;
        else
            gl_FrontColor = gl_Color;
    }
}
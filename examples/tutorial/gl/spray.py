# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
# Author:   Almar Klein & Nicolas P .Rougier
# Date:     04/03/2014
# Topic:    Fireworks !
# Keywords: oarticles, gl, sprites
# -----------------------------------------------------------------------------
"""
Example demonstrating simulation of fireworks using point sprites.
(adapted from the "OpenGL ES 2.0 Programming Guide")

This example demonstrates a series of explosions that last one second. The
visualization during the explosion is highly optimized using a Vertex Buffer
Object (VBO). After each explosion, vertex data for the next explosion are
calculated, such that each explostion is unique.
"""
import numpy as np

from vispy import app
from vispy.gloo import gl


vertex_code = """
#version 120
uniform float time;
uniform vec3 center;
attribute float lifetime;
attribute float age;
attribute vec3 start;
attribute float visible;
varying float v_lifetime;
void main () {
    if (0 < age && age < lifetime) {
        gl_Position.xyz = start + vec3(0, -1.5*age*age, 0);
        gl_Position.w = 1.0;
        //gl_Position.y = -1.5 * age * age;
    } else {
        // invisible
        gl_Position = vec4(-1000, -1000, 0, 0);
        //gl_Position = start;
        
    }
    v_lifetime = clamp((age / lifetime), 0.0, 1.0);
    gl_PointSize = 25 + (v_lifetime * v_lifetime) * 40.0;
}
"""

fragment_code = """
#version 120

uniform vec4 color;
varying float v_lifetime;
void main()
{
    //float d = 1 - length(gl_PointCoord - vec2(.5,.5)) / (sqrt(2)/2);
    //gl_FragColor = d*color;
    //gl_FragColor.a = d;
    //gl_FragColor.a *= v_lifetime;
    float d1 = (length(gl_PointCoord.xy - vec2(0.5,0.15)));
    float d2 = (length(gl_PointCoord.xy - vec2(0.5,0.85)));
    float d = d1+d2;
    gl_FragColor = vec4(color.rgb, 3.*color.a*(1-d));
}
"""


class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, size=(800, 600), title='GL Fireworks',
                            keys='interactive')

    def on_initialize(self, event):
        # Build & activate program
        self.program = gl.glCreateProgram()
        vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(vertex, vertex_code)
        gl.glShaderSource(fragment, fragment_code)
        gl.glCompileShader(vertex)
        gl.glCompileShader(fragment)
        gl.glAttachShader(self.program, vertex)
        gl.glAttachShader(self.program, fragment)
        gl.glLinkProgram(self.program)
        gl.glDetachShader(self.program, vertex)
        gl.glDetachShader(self.program, fragment)
        gl.glUseProgram(self.program)

        # Build vertex buffer
        n = 100
        self.data = np.zeros(n, dtype=[('lifetime', np.float32, 1),
                                       ('age',    np.float32, 1),
                                       ('start',    np.float32, 3),
                                       ('visible',      np.float32, 1)])
        vbuffer = gl.glCreateBuffer()
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbuffer)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.data, gl.GL_DYNAMIC_DRAW)

        # Bind buffer attributes
        stride = self.data.strides[0]

        offset = 0
        loc = gl.glGetAttribLocation(self.program, "lifetime")
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, 1, gl.GL_FLOAT, False, stride, offset)

        offset += self.data.dtype["lifetime"].itemsize
        loc = gl.glGetAttribLocation(self.program, "age")
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, 1, gl.GL_FLOAT, False, stride, offset)
        
        offset += self.data.dtype["age"].itemsize
        loc = gl.glGetAttribLocation(self.program, "start")
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, 3, gl.GL_FLOAT, False, stride, offset)

        offset += self.data.dtype["start"].itemsize
        loc = gl.glGetAttribLocation(self.program, "visible")
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, 3, gl.GL_FLOAT, False, stride, offset)

        # OpenGL initalization
        self.elapsed_time = 0
        gl.glClearColor(0, 0, 0, 1)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
        gl.glEnable(34370)  # gl.GL_VERTEX_PROGRAM_POINT_SIZE
        gl.glEnable(34913)  # gl.GL_POINT_SPRITE
        gl.glViewport(0, 0, *self.physical_size)
        self.new_explosion()
        self.timer = app.Timer('auto', self.on_timer, start=True)

    def on_draw(self, event):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glDrawArrays(gl.GL_POINTS, 0, len(self.data))

    def on_resize(self, event):
        gl.glViewport(0, 0, *event.physical_size)

    def on_timer(self, event):

        n = len(self.data)
        self.elapsed_time = 1. / 30.
        self.data["age"] += self.elapsed_time
        self.data["age"] %= self.data["lifetime"]
        #print(np.ndarray.sum(self.data["start"]))
        
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.data, gl.GL_DYNAMIC_DRAW)
        
        loc = gl.glGetUniformLocation(self.program, "time")
        gl.glUniform1f(loc, self.elapsed_time)
        self.update()

    def new_explosion(self):
        n = len(self.data)
        color = np.ones(4) #np.random.uniform(0.1, 0.9, 4).astype(np.float32)
        color[3] = 1.0 #/ n ** 0.08
        loc = gl.glGetUniformLocation(self.program, "color")
        gl.glUniform4f(loc, *color)

        center = np.zeros(3)*.5 # np.random.uniform(-0.5, 0.5, 3)
        loc = gl.glGetUniformLocation(self.program, "center")
        gl.glUniform3f(loc, *center)

        self.data['lifetime'] = np.random.normal(1.0, 0.005, (n,))
        self.data["age"] = np.random.normal(0, 0.002, (n,)) + np.arange(-n, 0)*1./90
        self.data['start'] = np.random.normal(0.0, 0.002, (n, 3))
        self.data['visible'][:] = 0. #np.random.normal(0.0, 0.002, (n, 3))
        #self.data['end'][:,1] -= 1 #np.random.normal(0.0, .002, (n, 3))
        gl.glBufferData(gl.GL_ARRAY_BUFFER, self.data, gl.GL_DYNAMIC_DRAW)

if __name__ == '__main__':
    c = Canvas()
    #c.measure_fps()
    c.show()
    app.run()

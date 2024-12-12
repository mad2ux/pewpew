from Range import logic, render, types
from bgl import *

render.setMipmapping(0)

VERTEX_SHADER = """
uniform float width;
uniform float height;
uniform float pixelSize;

varying vec4 v_color;
varying vec3 v_lighting;
varying vec2 v_uv;
varying vec2 v_reflect;
varying float v_n;

void main() {
	// Snap vertex to pixel
	float ps = pixelSize;
	if (ps <= 0) { ps = 1.0; }
	else if (ps >= 10.0) { ps = 10.0; }

	float pw = width / ps;
	float ph = height / ps;
	vec4 P = gl_ModelViewMatrix * gl_Vertex;
	vec4 snap = gl_ModelViewProjectionMatrix * gl_Vertex;
	vec4 vertex = snap;
	vertex.xyz = snap.xyz / snap.w;
	vertex.x = floor(pw * vertex.x) / pw;
	vertex.y = floor(ph * vertex.y) / ph;
	vertex.xyz *= snap.w;

	// Basic vertex lighting
	vec3 N = normalize(gl_NormalMatrix * gl_Normal);
	vec3 V = -normalize(P.xyz);
	vec3 L = vec3(0.0);
	float attenuation = 1.0;
	vec3 lighting = gl_LightModel.ambient.rgb;

	for (int i = 0; i < gl_MaxLights; i++) {
		if (gl_LightSource[i].diffuse.a == 0.0) { continue; }
		if (0.0 == gl_LightSource[i].position.w) { // SUN
			attenuation = 1.0;
			L = normalize(gl_LightSource[i].position.xyz);
		} else { // POINT
			vec3 PL = (gl_LightSource[i].position - P).xyz;
			float distance = length(PL);
			attenuation = 1.0 / (distance + 0.0001);
			L = normalize(PL);
		}
		// TODO: SPOT
		float NdotL = dot(N, L);
		vec3 diff = attenuation 
					* gl_LightSource[i].diffuse.rgb
					* max(NdotL, 0.0);
		diff = clamp(diff, 0.0, 1.0);

		vec3 spec = vec3(0.0);
		if (NdotL >= 0.0) {
			spec = attenuation 
				* gl_LightSource[i].specular.rgb
				* gl_FrontMaterial.specular.rgb
				* pow(max(0.0, dot(reflect(-L, N), V)), gl_FrontMaterial.shininess);
			spec = clamp(spec, 0.0, 1.0);
		}
		lighting += clamp(diff + spec, 0.0, 1.0);
	}

	// Affine texture mapping
	float s = (lighting.r + lighting.g + lighting.b) / 3.0;
	float distance = length(P) + 0.0001;	
	vec4 affinePos = vertex;
	vec2 uv = gl_MultiTexCoord0.st;

	float vws = (vertex.w * (s * 8.0));
	uv *= distance + vws / distance / 2.0;

	gl_Position = vertex;
	v_color = gl_Color;
	v_lighting = lighting;
	v_n = distance + vws / distance / 2.0;
	v_uv = uv;

	vec3 R = reflect(V, N);
	float m = 2. * sqrt(
		pow(R.x, 2.0) +
		pow(R.y, 2.0) +
		pow(R.z + 1.0, 2.0)
	);
	v_reflect = (R.xy / m + 0.5) * distance + vws / distance / 2.0;
}
"""

FRAGMENT_SHADER = """
varying vec4 v_color;
varying vec3 v_lighting;
varying vec2 v_reflect;
varying vec2 v_uv;
varying float v_n;

uniform sampler2D tex0;
uniform sampler2D tex1;
uniform float tex0Enabled;
uniform float tex1Enabled;

void main() {
	vec4 tex = vec4(1.0);
	if (tex0Enabled >= 1.0) {
		tex *= texture2D(tex0, v_uv / vec2(v_n));
	}
	if (tex1Enabled >= 1.0) {
		vec4 col = texture2D(tex1, v_reflect / vec2(v_n));
		if (tex0Enabled >= 1.0) {
			tex += col;
		} else {
			tex.rgb *= mix(tex.rgb, col.rgb, col.a);
		}
	}
	tex.rgb = clamp(tex.rgb, 0.0, 1.0);
	gl_FragColor = vec4(v_lighting * v_color.rgb * tex.rgb, v_color.a * tex.a);
}
"""

class PSX_Shader(types.KX_Camera):
	def __init__(self, ob):
		self.__shaders = []
		self.__lightStatus = [False] * 16
		self.__pixelSize = 4

		sce = self.scene
		for obj in sce.objects:
			if isinstance(obj, types.KX_GameObject):
				for mesh in obj.meshes:
					for material in mesh.materials:
						shader = material.getShader()
						shader.setSource(VERTEX_SHADER, FRAGMENT_SHADER, True)
						shader.setUniform1f("width", render.getWindowWidth())
						shader.setUniform1f("height", render.getWindowHeight())
						shader.setUniform1f("pixelSize", self.__pixelSize)
						shader.setUniform1f("tex0Enabled", 0)
						shader.setUniform1f("tex1Enabled", 0)
						shader.setSampler("tex0", 0)
						shader.setSampler("tex1", 1)
						if material.textures[0] is not None:
							shader.setUniform1f("tex0Enabled", 1.0)
						if material.textures[1] is not None:
							shader.setUniform1f("tex1Enabled", 1.0)
						self.__shaders.append(shader)
		
		# Set all lights as disabled.
		# So the lights that are enabled for viewport shading
		# are disabled.
		lightCount = Buffer(GL_INT, 1)
		glGetIntegerv(GL_MAX_LIGHTS, lightCount)
		lightCount = lightCount[0]
		
		for i in range(lightCount):
			ocolor = Buffer(GL_FLOAT, 4, [0.0, 0.0, 0.0, 0.0])
			glLightfv(GL_LIGHT0+i, GL_DIFFUSE, ocolor)

	@property
	def pixelSize(self):
		return self.__pixelSize

	@pixelSize.setter
	def pixelSize(self, v):
		if v != self.__pixelSize:
			self.__pixelSize = v
			for shader in self.__shaders:
				shader.setUniform1f("pixelSize", self.__pixelSize)

def __s(cont):
	pass

def main(cont):
	if isinstance(cont.owner, types.KX_Camera):
		PSX_Shader(cont.owner)
		cont.script = __name__ + ".__s"
	else:
		print("ERROR: The PSX Shader must be applied to a Camera!")
		logic.endGame()

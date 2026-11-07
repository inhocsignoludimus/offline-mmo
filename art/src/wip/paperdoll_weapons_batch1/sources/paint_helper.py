from PIL import Image
import numpy as np,cv2
def paint(path):
 a=np.array(Image.open(path).convert('RGBA')).astype(np.float32)/255.;al=a[...,3:];rgb=a[...,:3]
 # painterly pass on straight colour: edge-preserving flattening of CG micro-noise, then gentle local contrast/unsharp
 u8=(np.clip(rgb,0,1)*255).astype(np.uint8)
 f=cv2.bilateralFilter(u8,7,18,5).astype(np.float32)/255.
 lab=cv2.cvtColor((f*255).astype(np.uint8),cv2.COLOR_RGB2LAB);cl=cv2.createCLAHE(1.6,(8,8));lab[...,0]=cl.apply(lab[...,0]);f=cv2.cvtColor(lab,cv2.COLOR_LAB2RGB).astype(np.float32)/255.
 bl=cv2.GaussianBlur(f,(0,0),1.6);f=np.clip(f+.45*(f-bl),0,1)
 # restrained highlights: soft shoulder above 0.78
 f=np.where(f>.78,.78+(f-.78)*.55,f)
 pm=np.concatenate([f*al,al],2)
 p=np.stack([np.array(Image.fromarray(pm[...,c]).resize((300,480),Image.Resampling.LANCZOS)) for c in range(4)],2);A=np.clip(p[...,3:],0,1);c=np.where(A>1e-5,p[...,:3]/np.maximum(A,1e-5),0)
 v=np.rint(np.clip(np.concatenate([c,A],2),0,1)*255).astype(np.uint8);v[v[...,3]==0]=0;return Image.fromarray(v,'RGBA')

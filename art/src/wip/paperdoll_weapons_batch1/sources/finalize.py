from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib
R=Path('/workspace/paperdoll_weapons_batch1');W=R/'work';D=R/'pkg';PV=D/'art/_preview';P=Path('/workspace/offline-mmo-art/pr_ready/paperdoll_pr23_fix/art/paperdoll')
from paint_helper import paint
items=['shortsword','dagger','hand_axe','mace','longbow','staff','wand','buckler'];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
qa={'renderer':'Cycles 96 + denoiser, CPU fixed 3 threads, Standard, 600x960 to300x480','static_only':True,'engine_test':False,'files':{},'grip_method':'approved open hand unchanged; body-alpha occlusion of shaft behind palm/fingers baked into item layers; neutral display not active grip','visual_review':'pending'}
small=Image.new('RGB',(8*160,560),(27,27,32));dr=ImageDraw.Draw(small)
for row,s in enumerate('mf'):
 out=D/'art/paperdoll'/s;out.mkdir(exist_ok=True);body=Image.open(P/s/'body.png').convert('RGBA');ba=np.array(body)[...,3]/255.;yy,xx=np.indices(ba.shape);gx,gy=(48,237) if s=='m' else (35,216);oc=ba*((xx>gx-16)&(xx<gx+16)&(yy>gy-11)&(yy<gy+16));big=Image.new('RGB',(8*310,515),(27,27,32));bd=ImageDraw.Draw(big);grips=Image.new('RGB',(8*160,230),(27,27,32));gd=ImageDraw.Draw(grips)
 for c,it in enumerate(items):
  final=body.copy();available=False
  for tag in ['hue','fixed']:
   f=W/f'{it}_{s}_{tag}_raw.png'
   if not f.exists():continue
   available=True;im=paint(f);a=np.array(im)
   if tag=='hue':
    l=np.rint(a[...,:3]@np.array([.299,.587,.114])).astype('uint8');a[...,:3]=l[...,None]
   if it!='buckler':a[...,3]=np.rint(a[...,3]*(1-oc)).astype('uint8')
   a[a[...,3]==0]=0;im=Image.fromarray(a,'RGBA');name=it+('_fixed' if tag=='fixed' else '')+'.png';im.save(out/name,optimize=True)
   qa['files'][str((out/name).relative_to(D))]={'size':im.size,'mode':im.mode,'bbox':im.getbbox(),'alpha_minmax':[int(a[...,3].min()),int(a[...,3].max())],'hue_chroma':int(np.ptp(a[...,:3][a[...,3]>128],axis=1).max()) if tag=='hue' else None,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()}
   if tag=='hue':
    b=a.astype(float);b[...,:3]*=np.array([150,108,72])/255;show=Image.fromarray(b.astype('uint8'))
   else:show=im
   final.alpha_composite(show)
  if not available:continue
  final.save(PV/f'{it}_{s}_on_body.png',optimize=True)
  b=Image.new('RGBA',(150,240),(27,27,32));b.alpha_composite(final.resize((150,240),Image.Resampling.LANCZOS));small.paste(b.convert('RGB'),(c*160,30+row*280));dr.text((c*160,10+row*280),s+'/'+it,font=font,fill='white')
  b=Image.new('RGBA',(300,480),(27,27,32));b.alpha_composite(final);big.paste(b.convert('RGB'),(c*310,25));bd.text((c*310,5),s+'/'+it,font=font,fill='white')
  gxx,gyy=((243,237) if s=='m' else (251,218)) if it=='buckler' else (gx,gy)
  box=(max(0,gxx-25),gyy-45,min(300,gxx+35),gyy+40);cr=final.crop(box);cr=cr.resize((150,210),Image.Resampling.NEAREST);b=Image.new('RGBA',cr.size,(27,27,32));b.alpha_composite(cr);grips.paste(b.convert('RGB'),(c*160,20));gd.text((c*160,3),s+'/'+it,font=font,fill='white')
 big.save(PV/f'weapons_batch1_300_{s}.png');grips.save(PV/f'weapons_batch1_grips_{s}.png')
small.save(PV/'weapons_batch1_smoke_150x240.png');(D/'QA.json').write_text(json.dumps(qa,indent=2));print('layers',len(qa['files']))

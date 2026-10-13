# Synthesised score for the showreel: 20 s @ 120 BPM, numpy only.
import numpy as np, wave, sys
sr=44100; D=20.0; N=int(sr*D); t=np.arange(N)/sr
rng=np.random.default_rng(7)
mix=np.zeros(N); L=np.zeros(N); Rr=np.zeros(N)
def add(buf,sig,t0,gain=1.):
    i=int(t0*sr); 
    if i>=len(buf): return
    sig=sig[:len(buf)-i]; buf[i:i+len(sig)]+=sig*gain
def env(n,a,d): x=np.arange(n)/sr; return np.minimum(x/max(a,1e-4),1)*np.exp(-x/d)
def kick():
    n=int(.45*sr); x=np.arange(n)/sr
    f=45+110*np.exp(-x*28); ph=2*np.pi*np.cumsum(f)/sr
    return np.sin(ph)*np.exp(-x*7.5)+.25*np.sin(2*ph*.5)*np.exp(-x*20)
def hat(open_=False):
    n=int((.25 if open_ else .06)*sr); x=np.arange(n)/sr
    s=rng.standard_normal(n); s=np.diff(s,prepend=0); s=np.diff(s,prepend=0)
    return s*np.exp(-x*(18 if open_ else 70))*.5
def clap():
    n=int(.2*sr); x=np.arange(n)/sr; s=rng.standard_normal(n)
    e=np.exp(-x*30)+.6*np.exp(-((x-.012)**2)*8e4)
    return np.diff(s,prepend=0)*e*.5
def riser(dur):
    n=int(dur*sr); x=np.arange(n)/sr; s=rng.standard_normal(n)
    for _ in range(2): s=np.diff(s,prepend=0)*.7+s*.3
    ph=2*np.pi*np.cumsum(200+2800*(x/dur)**2)/sr
    return (s*.5+np.sin(ph)*.4)*(x/dur)**2.2
def boom(dur=1.6,f0=70):
    n=int(dur*sr); x=np.arange(n)/sr
    return np.sin(2*np.pi*(f0*np.exp(-x*1.4)+28)*x)*np.exp(-x*2.2)
def reverb(sig,sec=1.8):
    n=int(sec*sr); ir=rng.standard_normal(n)*np.exp(-np.arange(n)/sr*3.2)
    ir=np.convolve(ir,np.ones(8)/8,'same')
    m=len(sig)+n; F=np.fft.rfft(sig,m)*np.fft.rfft(ir,m)
    return np.fft.irfft(F,m)[:len(sig)]*.15
beat=.5
kick_s=kick(); kick_env=np.zeros(N)
# kicks: 2.0 -> 18.5 (quarter notes), double-time fill 16-18
for b in np.arange(2.0,18.5,beat):
    add(mix,kick_s,b,.95); add(kick_env,np.exp(-np.arange(int(.4*sr))/sr*9),b)
# off-beat hats from 4s, 8ths from 8s
for b in np.arange(4.25,18.5,beat): add(L,hat(True),b,.5); add(Rr,hat(True),b,.5)
for b in np.arange(8.0,18.5,beat/2):
    p=.5*np.sin(b*3); add(L,hat(),b,.35*(1+p)); add(Rr,hat(),b,.35*(1-p))
# claps 8..16 on 2 & 4
for b in np.arange(8.5,16.0,1.0): add(mix,clap(),b,.55)
# sub bass pulsing A1 w/ sidechain, 4..18.5
bass=np.sin(2*np.pi*55*t)+.4*np.sin(2*np.pi*110*t)+.15*np.sin(2*np.pi*165*t)
g=np.clip(1-kick_env*.9,0,1); gate=((t>3.5)&(t<18.55)).astype(float)
gate=np.convolve(gate,np.ones(2000)/2000,'same')
mix+=bass*g*gate*.28
# arp: A minor pentatonic 16ths, 8..18, rising filter-ish via harmonics
notes=[57,60,64,67,69,72,76,79]; mf=lambda m:440*2**((m-69)/12)
step=beat/4; k=0
for tt in np.arange(8.0,18.0,step):
    m=notes[[0,2,4,3,5,7,4,6][k%8]]+(12 if (tt>12) else 0)
    n=int(.28*sr); x=np.arange(n)/sr; f=mf(m)
    br=.25+.75*min((tt-8)/6,1)
    s=np.sin(2*np.pi*f*x)+br*.5*np.sin(4*np.pi*f*x)+br*.25*np.sin(6*np.pi*f*x)
    s*=env(n,.003,.09)
    p=np.sin(tt*1.7)*.8
    add(L,s,tt,.11*(1+p)); add(Rr,s,tt,.11*(1-p))
    add(L,s,tt+.375,.06); add(Rr,s,tt+.5,.06)  # ping-pong echo
    k+=1
# pad: Am chord swell throughout, 0..20 (fills the opening and the breakdown)
for f,pan in [(110,-.4),(164.81,.3),(220,-.2),(261.63,.4),(329.63,0)]:
    s=np.sin(2*np.pi*f*t+np.sin(t*.7+f)*.5)+np.sin(2*np.pi*(f*1.004)*t)
    a=np.clip(t/3,0,1)*np.clip((20-t)/1.5,0,1)*(.35+.65*(t>16)*(t<18.5)+.0)
    a=np.where((t>3.8)&(t<16),.12,a*1.0)
    add(L,s*a*.05*(1-pan),0); add(Rr,s*a*.05*(1+pan),0)
# opening: sine drone swelling with a sweep, heartbeat soft kicks
sw=np.sin(2*np.pi*np.cumsum(60+60*np.clip(t/4,0,1)**3)/sr)*np.clip(t/3,0,1)*(t<4.2)*.18
mix+=sw
# scene boundary risers + hits (4,8,12,16)
for b in (4,8,12,16):
    r=riser(.9); add(L,r,b-.9,.22); add(Rr,r[::-1]*0+r,b-.9,.22)
    add(mix,boom(1.2,90),b,.55)
# intro: riser to first kick
r=riser(2.0); add(L,r,0,.14); add(Rr,r,0,.14)
# singularity: collapse suck (16..18.6) then impact
sk=riser(2.6); sk=sk*np.sin(2*np.pi*np.cumsum(np.linspace(900,60,len(sk)))/sr)*1.0
add(L,sk,16.0,.25); add(Rr,sk,16.0,.25)
add(mix,boom(2.8,60),18.6,1.1)
add(L,hat(True)*4,18.6,.9); add(Rr,hat(True)*4,18.6,.9)
# bell-ish tail at title
for i,m in enumerate([81,76,69]):
    n=int(2.2*sr); x=np.arange(n)/sr; f=mf(m)
    s=(np.sin(2*np.pi*f*x)+.4*np.sin(2*np.pi*f*2.76*x))*np.exp(-x*2.2)
    add(L,s,18.7+i*.25,.12); add(Rr,s,18.75+i*.25,.12)
# assemble, reverb send, master
L+=mix; Rr+=mix
wetL=reverb(L*.8); wetR=reverb(Rr*.8)
L+=wetL; Rr+=wetR
fade=np.clip(t/.05,0,1)*np.clip((20-t)/.8,0,1)
L*=fade; Rr*=fade
pk=max(np.abs(L).max(),np.abs(Rr).max()); L=np.tanh(L/pk*1.6)*.9; Rr=np.tanh(Rr/pk*1.6)*.9
pcm=(np.stack([L,Rr],1)*32767).astype('<i2')
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes()); w.close()
print('ok',pk)

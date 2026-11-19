"""Render a labeled step walkthrough from genuine Power BI screenshots. Requires ffmpeg."""
from pathlib import Path
import json, subprocess
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'docs/recordings/captures.json').read_text())
folder=ROOT/'docs/recordings'
fonts=[Path('C:/Windows/Fonts/arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
font=next((f for f in fonts if f.exists()),None)
font_option="fontfile='"+font.as_posix().replace(':',r'\:')+"':" if font else ''
for i,frame in enumerate(manifest['frames']):
    source=ROOT/frame['path']
    caption=folder/f'caption-{i}.txt'
    caption.write_text(f"{i+1}/{len(manifest['frames'])}  {frame['title']} | Actual Power BI capture - step walkthrough",encoding='utf-8')
    # Run in media folder so filter textfile paths are portable and contain no drive colon.
    vf=f"scale=1920:970:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:0:color=0x17232d,drawtext={font_option}textfile=caption-{i}.txt:fontcolor=white:fontsize=26:x=36:y=1010"
    subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(source),'-t','6','-vf',vf,'-r','24','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p',f'part-{i}.mp4'],cwd=folder,check=True)
parts=folder/'parts.txt'
parts.write_text(''.join(f"file 'part-{i}.mp4'\n" for i in range(len(manifest['frames']))))
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i','parts.txt','-c','copy','-movflags','+faststart','walkthrough.mp4'],cwd=folder,check=True)
for i in range(len(manifest['frames'])):
    (folder/f'part-{i}.mp4').unlink();(folder/f'caption-{i}.txt').unlink()
parts.unlink()
print(folder/'walkthrough.mp4')

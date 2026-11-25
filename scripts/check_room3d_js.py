"""Runtime check of static/room3d.js (Room3d.build / tip) with node and a mock of three.js.

The house comes from the core on a temp copy whose Wohnzimmer gets a floor covering, a zone and a skirting;
the project data stays unchanged. Prints the number of meshes per kind.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
home = tempfile.mkdtemp()
for folder in ("catalog", "house"):
    shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
os.environ["WEINGAERTEN_HOME"] = home
import weingaerten_core  # noqa: E402

path = os.path.join(home, "house", "storeys", "ground.json")
with open(path, encoding="utf-8") as handle:
    storey = json.load(handle)
room = next(r for r in storey["rooms"] if r["id"] == "room-wohnzimmer")
room["coverings"] = [
    {"id": "bel-wz", "surface": "floor", "assembly": "assembly:covering-parkett-eiche", "area": "room"},
    {"id": "bel-feld", "surface": "floor", "assembly": "assembly:covering-fliese-boden",
     "area": [[1.0, 6.0], [2.0, 6.0], [2.0, 7.0], [1.0, 7.0]]},
    {"id": "sockel", "surface": "wall", "assembly": "assembly:covering-sockelleiste-kiefer", "walls": "all", "z": [0, 0.06]}]
with open(path, "w", encoding="utf-8") as handle:
    json.dump(storey, handle, ensure_ascii=False, indent=2)
house = json.loads(weingaerten_core.handle(json.dumps({"command": "HOUSE"})))
shutil.rmtree(home, ignore_errors=True)

script = r"""
const window={};eval(require('fs').readFileSync(process.argv[2],'utf8'));const Room3d=window.Room3d;
const H=JSON.parse(require('fs').readFileSync(process.argv[3],'utf8'));
class Mesh{constructor(g,m){this.geometry=g;this.material=m;this.userData={}}}
const T={Mesh,MeshStandardMaterial:class{constructor(o){Object.assign(this,o)}},LineSegments:class{},EdgesGeometry:class{},LineBasicMaterial:class{}};
const group={items:[],add(o){this.items.push(o)}},pick=[];let prisms=0;
const prism=(pts,z0,h)=>{if(!(pts.length>=3&&h>0&&isFinite(z0)))throw new Error('bad prism '+JSON.stringify([pts,z0,h]));prisms++;return {pts,z0,h}};
Room3d.build(T,group,pick,H,prism,()=>true,{col:()=>'#ccc',transparent:false,coverings:true,shafts:true});
const kinds={};pick.forEach(m=>{kinds[m.userData.kind]=(kinds[m.userData.kind]||0)+1});
const tips=pick.slice(0,1).concat(pick.filter(m=>m.userData.kind==='shaft').slice(0,1)).map(m=>Room3d.tip(m.userData)[0][0]);
const holes=Room3d.minus([[0,0,4,4]],[[1,1,1,1]]);const area=holes.reduce((s,r)=>s+r[2]*r[3],0);
console.log(JSON.stringify({kinds,prisms,tips,minus_area:area,ceiling_holes:Room3d.ceilingHoles(H,'storey:ground',H.storeys.find(s=>s.id==='ground').ceilings[0].polygon).length}));
"""
tmp = tempfile.mkdtemp()
try:
    house_path, js_path = os.path.join(tmp, "house.json"), os.path.join(tmp, "check.js")
    with open(house_path, "w", encoding="utf-8") as handle:
        json.dump(house, handle)
    with open(js_path, "w", encoding="utf-8") as handle:
        handle.write(script)
    result = subprocess.run(["node", js_path, os.path.join(ROOT, "code", "weingaerten_web", "static", "room3d.js"), house_path],
                            capture_output=True, text=True)
    print(result.stdout or result.stderr)
    sys.exit(result.returncode)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

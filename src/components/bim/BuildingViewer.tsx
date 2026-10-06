import { Canvas, type ThreeEvent } from "@react-three/fiber";
import { Environment, Lightformer, OrbitControls, Grid } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";
import { bounds, type BuildingModel, type ElementRef, type Level, type Wall } from "@/lib/bim/schema";

type Props = { model: BuildingModel; hiddenLevels: string[]; selected: ElementRef | null; onSelect: (r: ElementRef | null) => void; showRoof: boolean };

const C = { wallExt: "#e9e2d4", wallInt: "#f6f2ea", door: "#8a5a3b", glass: "#9fd3e6", roof: "#b5523b", sel: "#f5b400", floor: ["#d9c7a7", "#c9d8c5", "#cfd6e4", "#e6d2c9", "#d6cfe3"] };

function pick(e: ThreeEvent<MouseEvent>, ref: ElementRef, onSelect: Props["onSelect"]) { e.stopPropagation(); onSelect(ref); }

function WallMesh({ wall, level, model, selected, onSelect }: { wall: Wall; level: Level; model: BuildingModel; selected: ElementRef | null; onSelect: Props["onSelect"] }) {
  const [x1, y1] = wall.start, [x2, y2] = wall.end;
  const len = Math.hypot(x2 - x1, y2 - y1);
  const h = wall.height ?? level.height;
  const angle = -Math.atan2(y2 - y1, x2 - x1);
  const ops = model.openings.filter((o) => o.wallId === wall.id).sort((a, b) => a.offset - b.offset);
  // segments [start, end, bottom, top] le long du mur
  const segs: [number, number, number, number][] = [];
  let cur = 0;
  for (const o of ops) {
    const s = Math.max(0, o.offset), e = Math.min(len, o.offset + o.width);
    if (s > cur) segs.push([cur, s, 0, h]);
    if (o.sill > 0) segs.push([s, e, 0, o.sill]);
    if (o.sill + o.height < h) segs.push([s, e, o.sill + o.height, h]);
    cur = Math.max(cur, e);
  }
  if (cur < len) segs.push([cur, len, 0, h]);
  const isSel = selected?.kind === "mur" && selected.id === wall.id;
  const color = isSel ? C.sel : wall.type === "exterieur" ? C.wallExt : C.wallInt;
  return (
    <group position={[x1, level.elevation, -y1]} rotation={[0, angle, 0]}>
      {segs.map(([s, e, b, t], i) => (
        <mesh key={i} position={[(s + e) / 2, (b + t) / 2, 0]} castShadow receiveShadow onClick={(ev) => pick(ev, { kind: "mur", id: wall.id }, onSelect)}>
          <boxGeometry args={[e - s, t - b, wall.thickness]} />
          <meshStandardMaterial color={color} roughness={0.9} />
        </mesh>
      ))}
      {ops.map((o) => {
        const sel = selected?.id === o.id;
        const isDoor = o.kind === "porte";
        return (
          <mesh key={o.id} position={[o.offset + o.width / 2, o.sill + o.height / 2, 0]} onClick={(ev) => pick(ev, { kind: o.kind, id: o.id }, onSelect)}>
            <boxGeometry args={[o.width, o.height, isDoor ? 0.05 : 0.03]} />
            <meshStandardMaterial color={sel ? C.sel : isDoor ? C.door : C.glass} transparent={!isDoor} opacity={isDoor ? 1 : 0.55} roughness={isDoor ? 0.7 : 0.05} metalness={isDoor ? 0 : 0.3} />
          </mesh>
        );
      })}
    </group>
  );
}

function RoomFloor({ room, level, idx, selected, onSelect }: { room: BuildingModel["rooms"][number]; level: Level; idx: number; selected: ElementRef | null; onSelect: Props["onSelect"] }) {
  const geo = useMemo(() => {
    const shape = new THREE.Shape(room.polygon.map(([x, y]) => new THREE.Vector2(x, y)));
    return new THREE.ExtrudeGeometry(shape, { depth: 0.12, bevelEnabled: false });
  }, [room.polygon]);
  const sel = selected?.kind === "piece" && selected.id === room.id;
  return (
    <mesh geometry={geo} rotation={[-Math.PI / 2, 0, 0]} position={[0, level.elevation - 0.12, 0]} receiveShadow onClick={(e) => pick(e, { kind: "piece", id: room.id }, onSelect)}>
      <meshStandardMaterial color={sel ? C.sel : (C.floor[idx % C.floor.length] ?? "#d9c7a7")} roughness={0.8} />
    </mesh>
  );
}

function Roof({ model, selected, onSelect }: { model: BuildingModel; selected: ElementRef | null; onSelect: Props["onSelect"] }) {
  const roof = model.roof!;
  const top = model.levels.find((l) => l.id === roof.levelId) ?? [...model.levels].sort((a, b) => b.elevation - a.elevation)[0]!;
  const b = bounds(model, top.id);
  const o = roof.overhang;
  const minX = b.minX - o, maxX = b.maxX + o, minY = b.minY - o, maxY = b.maxY + o;
  const base = top.elevation + top.height;
  const geo = useMemo(() => {
    const w = maxX - minX, d = maxY - minY;
    const rise = Math.tan((roof.pitch * Math.PI) / 180) * (Math.min(w, d) / 2);
    if (roof.type === "plat") return new THREE.BoxGeometry(w, 0.25, d).translate((minX + maxX) / 2, base + 0.125, -(minY + maxY) / 2);
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    const g = new THREE.BufferGeometry();
    const P = (x: number, y: number, z: number) => [x, base + z, -y];
    let v: number[][];
    if (roof.type === "deux_pans") {
      const ridgeAlongX = w >= d;
      const r1 = ridgeAlongX ? P(minX, cy, rise) : P(cx, minY, rise), r2 = ridgeAlongX ? P(maxX, cy, rise) : P(cx, maxY, rise);
      const a = P(minX, minY, 0), bb = P(maxX, minY, 0), c = P(maxX, maxY, 0), dd = P(minX, maxY, 0);
      v = ridgeAlongX ? [a, bb, r2, a, r2, r1, c, dd, r1, c, r1, r2, a, r1, dd, bb, c, r2] : [bb, c, r2, bb, r2, r1, dd, a, r1, dd, r1, r2, a, bb, r1, c, dd, r2];
    } else {
      const inset = Math.min(w, d) / 2;
      const ridgeAlongX = w >= d;
      const r1 = ridgeAlongX ? P(minX + inset, cy, rise) : P(cx, minY + inset, rise), r2 = ridgeAlongX ? P(maxX - inset, cy, rise) : P(cx, maxY - inset, rise);
      const a = P(minX, minY, 0), bb = P(maxX, minY, 0), c = P(maxX, maxY, 0), dd = P(minX, maxY, 0);
      v = ridgeAlongX ? [a, bb, r2, a, r2, r1, c, dd, r1, c, r1, r2, dd, a, r1, bb, c, r2] : [bb, c, r2, bb, r2, r1, dd, a, r1, dd, r1, r2, a, bb, r1, c, dd, r2];
    }
    g.setAttribute("position", new THREE.Float32BufferAttribute(v.flat(), 3));
    g.computeVertexNormals();
    return g;
  }, [minX, maxX, minY, maxY, base, roof.type, roof.pitch]);
  const sel = selected?.kind === "toiture";
  return (
    <mesh geometry={geo} castShadow onClick={(e) => pick(e, { kind: "toiture", id: "toiture" }, onSelect)}>
      <meshStandardMaterial color={sel ? C.sel : C.roof} side={THREE.DoubleSide} roughness={0.85} />
    </mesh>
  );
}

export default function BuildingViewer({ model, hiddenLevels, selected, onSelect, showRoof }: Props) {
  const b = bounds(model);
  const cx = (b.minX + b.maxX) / 2, cy = (b.minY + b.maxY) / 2;
  const size = Math.max(b.maxX - b.minX, b.maxY - b.minY, 6);
  const levels = model.levels.filter((l) => !hiddenLevels.includes(l.id));
  return (
    <Canvas shadows dpr={[1, 2]} camera={{ position: [cx + size, size * 0.9, -cy + size * 1.1], fov: 45 }} onPointerMissed={() => onSelect(null)}>
      <color attach="background" args={["#e8edf2"]} />
      <hemisphereLight args={["#ffffff", "#b9a98f", 0.6]} />
      <directionalLight position={[cx + 15, 25, -cy + 10]} intensity={1.6} castShadow shadow-mapSize={[2048, 2048]} shadow-camera-left={-30} shadow-camera-right={30} shadow-camera-top={30} shadow-camera-bottom={-30} />
      <Environment resolution={64}>
        <Lightformer intensity={2} position={[0, 8, 0]} scale={[10, 10, 1]} rotation-x={Math.PI / 2} />
        <Lightformer intensity={1} color="#cde" position={[-8, 2, -2]} rotation-y={Math.PI / 2} scale={[20, 2, 1]} />
      </Environment>
      <group>
        {levels.map((lvl) => (
          <group key={lvl.id}>
            {model.rooms.filter((r) => r.levelId === lvl.id).map((r, i) => <RoomFloor key={r.id} room={r} level={lvl} idx={i} selected={selected} onSelect={onSelect} />)}
            {model.walls.filter((w) => w.levelId === lvl.id).map((w) => <WallMesh key={w.id} wall={w} level={lvl} model={model} selected={selected} onSelect={onSelect} />)}
          </group>
        ))}
        {showRoof && model.roof && hiddenLevels.length === 0 && <Roof model={model} selected={selected} onSelect={onSelect} />}
      </group>
      <mesh rotation-x={-Math.PI / 2} position={[cx, -0.13, -cy]} receiveShadow>
        <planeGeometry args={[size * 6, size * 6]} />
        <meshStandardMaterial color="#c8cfb8" roughness={1} />
      </mesh>
      <Grid position={[cx, -0.12, -cy]} args={[size * 4, size * 4]} cellSize={1} sectionSize={5} cellColor="#9aa59a" sectionColor="#6d7a8a" fadeDistance={size * 4} infiniteGrid={false} />
      <OrbitControls target={[cx, 1.5, -cy]} makeDefault maxPolarAngle={Math.PI / 2.05} />
    </Canvas>
  );
}

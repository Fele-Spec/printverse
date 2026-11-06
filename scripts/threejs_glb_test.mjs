/**
 * Three.js runtime check without a browser: parse the exported GLB with the real
 * GLTFLoader, walk the scene graph, and compute its world bounding box.
 * Browser screenshot testing is separate and may be blocked by the sandbox.
 */
import fs from 'node:fs';
import path from 'node:path';

const THREE = await import('../frontend/node_modules/three/build/three.module.js');
const { GLTFLoader } = await import('../frontend/node_modules/three/examples/jsm/loaders/GLTFLoader.js');

const file = 'assets/processed/filament_card.glb';
const buffer = fs.readFileSync(file);
const loader = new GLTFLoader();

const result = await new Promise((resolve) => {
  loader.parse(buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength), '', (gltf) => {
    let meshes = 0;
    let triangles = 0;
    const names = [];
    gltf.scene.traverse((obj) => {
      if (obj.isMesh) {
        meshes += 1;
        names.push(obj.name);
        const g = obj.geometry;
        triangles += g.index ? g.index.count / 3 : (g.attributes.position?.count ?? 0) / 3;
      }
    });
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    resolve({
      ok: meshes > 0,
      file,
      bytes: buffer.length,
      three_version: THREE.REVISION,
      meshes,
      mesh_names: names,
      triangles: Math.round(triangles),
      size_mm: [size.x, size.y, size.z].map((n) => Number(n.toFixed(3))),
      center_mm: [center.x, center.y, center.z].map((n) => Number(n.toFixed(3))),
      animations: gltf.animations.length,
    });
  }, (err) => resolve({ ok: false, file, error: String(err) }));
});

fs.mkdirSync('docs/reports', { recursive: true });
fs.writeFileSync('docs/reports/threejs_glb_test.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify(result, null, 2));
if (!result.ok) process.exit(1);

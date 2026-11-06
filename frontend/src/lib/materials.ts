export type MaterialId =
  | 'anodized_aluminum' | 'brushed_aluminum' | 'stainless_steel' | 'black_oxide_steel'
  | 'rubber_belt' | 'engineering_plastic' | 'acrylic_panel' | 'textured_print_surface'
  | 'brass_nozzle' | 'silicone_cable' | 'painted_metal' | 'powder_coated';

export type MaterialSpec = {
  id: MaterialId;
  label: string;
  color: string;
  metalness: number;
  roughness: number;
  transmission?: number;
  thickness?: number;
  ior?: number;
  clearcoat?: number;
  clearcoatRoughness?: number;
  transparent?: boolean;
  opacity?: number;
  depthWrite?: boolean;
};

export const MATERIALS: Record<MaterialId, MaterialSpec> = {
  anodized_aluminum: { id: 'anodized_aluminum', label: 'Anodized Aluminum', color: '#20272c', metalness: 0.88, roughness: 0.34, clearcoat: 0.12, clearcoatRoughness: 0.4 },
  brushed_aluminum: { id: 'brushed_aluminum', label: 'Brushed Aluminum', color: '#b8c1c6', metalness: 0.94, roughness: 0.27 },
  stainless_steel: { id: 'stainless_steel', label: 'Stainless Steel', color: '#c6cdd0', metalness: 0.96, roughness: 0.21 },
  black_oxide_steel: { id: 'black_oxide_steel', label: 'Black Oxide Steel', color: '#171a1c', metalness: 0.72, roughness: 0.4 },
  rubber_belt: { id: 'rubber_belt', label: 'Rubber Belt', color: '#101214', metalness: 0.02, roughness: 0.82 },
  engineering_plastic: { id: 'engineering_plastic', label: 'Engineering Plastic', color: '#20262a', metalness: 0.04, roughness: 0.56, clearcoat: 0.08 },
  acrylic_panel: { id: 'acrylic_panel', label: 'Acrylic Panel', color: '#8caeb8', metalness: 0.01, roughness: 0.08, transmission: 0.62, thickness: 3, ior: 1.49, transparent: true, opacity: 0.24, depthWrite: false },
  textured_print_surface: { id: 'textured_print_surface', label: 'Textured Print Surface', color: '#a9a396', metalness: 0.03, roughness: 0.7 },
  brass_nozzle: { id: 'brass_nozzle', label: 'Brass Nozzle', color: '#b88645', metalness: 0.9, roughness: 0.3 },
  silicone_cable: { id: 'silicone_cable', label: 'Silicone Cable', color: '#1b1f22', metalness: 0.01, roughness: 0.74 },
  painted_metal: { id: 'painted_metal', label: 'Painted Metal', color: '#263139', metalness: 0.5, roughness: 0.44, clearcoat: 0.22, clearcoatRoughness: 0.35 },
  powder_coated: { id: 'powder_coated', label: 'Powder Coated Surface', color: '#1d2429', metalness: 0.24, roughness: 0.63, clearcoat: 0.04 },
};

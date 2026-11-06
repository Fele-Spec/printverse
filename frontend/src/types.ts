export type Move = [
  x0: number, y0: number, x1: number, y1: number, z: number,
  de: number, dt: number, typeIndex: number, travel: 0 | 1, layer: number,
];

export type ToolpathMeta = {
  file: string;
  bytes: number;
  layers: number;
  layer_z: Record<string, number>;
  mass_g: number;
  filament_mm: number;
  volume_mm3: number;
  diameter_mm: number;
  density_g_cm3: number;
  time_s: number;
  computed_time_s: number;
  bounds: { min: [number, number, number]; max: [number, number, number] };
  commands: Record<string, number>;
  move_count: number;
  types: string[];
  source: string;
};

export type Toolpath = { meta: ToolpathMeta; moves: Move[] };

export type Job = {
  id: string;
  name: string;
  status: string;
  mass_g: number;
  layers: number | null;
  time_s: number | null;
  free_print: boolean;
  reserved_g: number;
  warnings: string | null;
  toolpath_url: string;
  model_url: string;
  gcode_url: string;
};

export type Wallet = {
  user: string;
  name: string;
  role: string;
  balance_mg: number;
  balance_g: number;
  first_print_available: boolean;
  ledger: Array<{ kind: string; mg: number; operation_id: string; job_id: string | null; reason: string; created_at: string }>;
};

export type CollectionItem = {
  id: number;
  user_id: string;
  job_id: string;
  name: string;
  mass_mg: number;
  model_path: string;
  created_at: string;
};

export type PrintTick = {
  time: number;
  progress: number;
  layer: number;
  toolhead: { x: number; y: number };
  bedZ: number;
  deposited: number;
  mass_g: number;
};

const COLORS: Record<string, string> = {
  'Outer wall': '#79f2c0',
  'Inner wall': '#42c7a5',
  Perimeter: '#79f2c0',
  'External perimeter': '#b9ffdf',
  'Top surface': '#ffd166',
  'Bottom surface': '#f6a55c',
  'Internal solid infill': '#ed8f5b',
  'Sparse infill': '#5fa8ff',
  'Internal Bridge': '#d78bff',
  Bridge: '#d78bff',
  Travel: '#3c5360',
  Custom: '#8aa4b4',
  Unknown: '#8aa4b4',
};

export function colorForType(name: string): string {
  return COLORS[name] ?? '#8aa4b4';
}

export function cssColorForType(name: string): string {
  return colorForType(name);
}

import type {TemplateId} from './contracts';

export const DESIGN = {
  colors: {
    ink: '#172033',
    mist: '#F7F5F1',
    surface: '#FFFFFF',
    pink: '#D98D9D',
    coral: '#FFB4A2',
    blue: '#6C9BD2',
    amber: '#E8B84E',
    muted: '#E6EAF0',
    code: '#172033',
  },
  safe: {top: 150, right: 80, bottom: 300, left: 80},
  radius: {panel: 36, chip: 18, caption: 20},
  font: 'Microsoft YaHei, sans-serif',
} as const;

export const templateAccent = (template: TemplateId) => ({
  'protocol-frame': DESIGN.colors.blue,
  'code-explainer': DESIGN.colors.pink,
  'flow-diagram': DESIGN.colors.amber,
  'engineering-case': DESIGN.colors.coral,
}[template]);

export const templateLabel = (template: TemplateId) => ({
  'protocol-frame': '协议帧拆解',
  'code-explainer': '代码边界',
  'flow-diagram': '任务流转',
  'engineering-case': '工程案例',
}[template]);

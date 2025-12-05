// src/modules/materialToolMatcher.js
// 材料-刀具智能匹配模块

// 材料数据库
const materialDatabase = {
  // 钢材
  'steel': {
    name: '钢',
    hardness: { min: 150, max: 600, unit: 'HB' },
    tensileStrength: { min: 400, max: 2000, unit: 'MPa' },
    defaultToolMaterial: 'carbide',
    recommendedCuttingSpeed: { 
      rough: { min: 80, max: 150, unit: 'm/min' },
      finish: { min: 120, max: 200, unit: 'm/min' }
    }
  },
  'stainless_steel': {
    name: '不锈钢',
    hardness: { min: 150, max: 300, unit: 'HB' },
    tensileStrength: { min: 500, max: 800, unit: 'MPa' },
    defaultToolMaterial: 'carbide',
    recommendedCuttingSpeed: {
      rough: { min: 60, max: 120, unit: 'm/min' },
      finish: { min: 100, max: 160, unit: 'm/min' }
    }
  },
  'aluminum': {
    name: '铝',
    hardness: { min: 15, max: 150, unit: 'HB' },
    tensileStrength: { min: 70, max: 300, unit: 'MPa' },
    defaultToolMaterial: 'carbide',
    recommendedCuttingSpeed: {
      rough: { min: 200, max: 1000, unit: 'm/min' },
      finish: { min: 300, max: 1200, unit: 'm/min' }
    }
  },
  'copper': {
    name: '铜',
    hardness: { min: 35, max: 100, unit: 'HB' },
    tensileStrength: { min: 200, max: 300, unit: 'MPa' },
    defaultToolMaterial: 'hss',
    recommendedCuttingSpeed: {
      rough: { min: 100, max: 300, unit: 'm/min' },
      finish: { min: 150, max: 400, unit: 'm/min' }
    }
  },
  'plastic': {
    name: '塑料',
    hardness: { min: 10, max: 50, unit: 'HB' },
    tensileStrength: { min: 20, max: 100, unit: 'MPa' },
    defaultToolMaterial: 'carbide',
    recommendedCuttingSpeed: {
      rough: { min: 150, max: 500, unit: 'm/min' },
      finish: { min: 200, max: 600, unit: 'm/min' }
    }
  },
  'titanium': {
    name: '钛合金',
    hardness: { min: 300, max: 450, unit: 'HB' },
    tensileStrength: { min: 900, max: 1200, unit: 'MPa' },
    defaultToolMaterial: 'carbide',
    recommendedCuttingSpeed: {
      rough: { min: 30, max: 60, unit: 'm/min' },
      finish: { min: 50, max: 80, unit: 'm/min' }
    }
  }
};

// 刀具数据库
const toolDatabase = {
  'hss': {
    name: '高速钢刀具',
    materials: ['steel', 'aluminum', 'copper', 'plastic'],
    coating: 'none',
    maxRPM: 8000,
    maxCuttingSpeed: 150,
    feedPerTooth: { steel: 0.05, aluminum: 0.15, copper: 0.12, plastic: 0.2 }
  },
  'carbide_uncoated': {
    name: '未涂层硬质合金刀具',
    materials: ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic', 'titanium'],
    coating: 'none',
    maxRPM: 15000,
    maxCuttingSpeed: 300,
    feedPerTooth: { steel: 0.08, stainless_steel: 0.06, aluminum: 0.18, copper: 0.15, plastic: 0.25, titanium: 0.03 }
  },
  'carbide_ticn': {
    name: 'TiCN涂层硬质合金刀具',
    materials: ['steel', 'stainless_steel', 'aluminum', 'copper', 'titanium'],
    coating: 'TiCN',
    maxRPM: 20000,
    maxCuttingSpeed: 400,
    feedPerTooth: { steel: 0.10, stainless_steel: 0.08, aluminum: 0.20, copper: 0.18, titanium: 0.04 }
  },
  'carbide_alcrn': {
    name: 'AlCrN涂层硬质合金刀具',
    materials: ['steel', 'stainless_steel', 'titanium'],
    coating: 'AlCrN',
    maxRPM: 25000,
    maxCuttingSpeed: 500,
    feedPerTooth: { steel: 0.12, stainless_steel: 0.10, titanium: 0.05 }
  }
};

// 特征类型到刀具映射
const featureToToolMapping = {
  'hole': {
    'center_drill': ['steel', 'stainless_steel', 'aluminum', 'copper'],
    'twist_drill': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic'],
    'step_drill': ['aluminum', 'copper', 'plastic'],
    'reamer': ['steel', 'stainless_steel', 'aluminum', 'copper']
  },
  'counterbore': {
    'counterbore_tool': ['steel', 'stainless_steel', 'aluminum', 'copper'],
    'spotface_tool': ['steel', 'stainless_steel', 'aluminum', 'copper']
  },
  'pocket': {
    'endmill': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic', 'titanium'],
    'face_mill': ['steel', 'aluminum', 'copper', 'plastic']
  },
  'slot': {
    'slot_drill': ['steel', 'aluminum', 'copper'],
    'side_mill': ['steel', 'aluminum', 'copper', 'plastic']
  },
  'face_mill': {
    'face_mill': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic']
  },
  'thread': {
    'tap': ['steel', 'aluminum', 'copper', 'plastic'],
    'thread_mill': ['steel', 'stainless_steel', 'aluminum', 'copper']
  }
};

// 推荐加工参数
function recommendMachiningParameters(materialType, toolType, featureType, featureSize = {}) {
  const material = materialDatabase[materialType];
  const tool = toolDatabase[toolType];
  
  if (!material || !tool) {
    return null;
  }
  
  // 基础参数计算
  const baseCuttingSpeed = material.recommendedCuttingSpeed.finish.min;
  const feedPerTooth = tool.feedPerTooth[materialType] || 0.1;
  
  // 根据特征类型调整参数
  let cuttingSpeed = baseCuttingSpeed;
  let spindleSpeed = 0;
  let feedRate = 0;
  
  // 计算主轴转速 (RPM = (Cutting Speed * 1000) / (π * Tool Diameter))
  const toolDiameter = featureSize.diameter || 6; // 默认6mm
  spindleSpeed = Math.round((cuttingSpeed * 1000) / (Math.PI * toolDiameter));
  
  // 限制主轴转速不超过刀具最大RPM
  spindleSpeed = Math.min(spindleSpeed, tool.maxRPM);
  
  // 计算进给率 (Feed Rate = Spindle Speed * Feed Per Tooth * Number of Flutes)
  const numberOfFlutes = featureSize.flutes || 2; // 默认2刃
  feedRate = Math.round(spindleSpeed * feedPerTooth * numberOfFlutes);
  
  // 根据特征类型进一步调整
  switch (featureType) {
    case 'hole':
      // 钻孔时降低主轴转速和进给率
      spindleSpeed = Math.round(spindleSpeed * 0.7);
      feedRate = Math.round(feedRate * 0.6);
      break;
    case 'pocket':
      // 铣削口袋时使用中等参数
      spindleSpeed = Math.round(spindleSpeed * 0.9);
      feedRate = Math.round(feedRate * 0.85);
      break;
    case 'face_mill':
      // 面铣时可以使用较高参数
      spindleSpeed = Math.round(spindleSpeed * 0.95);
      feedRate = Math.round(feedRate * 0.9);
      break;
    case 'thread':
      // 攻丝时使用较低参数
      spindleSpeed = Math.round(spindleSpeed * 0.5);
      feedRate = Math.round(feedRate * 0.4);
      break;
    default:
      // 其他特征类型使用计算值
  }
  
  return {
    spindleSpeed: spindleSpeed,
    feedRate: feedRate,
    cuttingSpeed: cuttingSpeed,
    toolDiameter: toolDiameter,
    numberOfFlutes: numberOfFlutes,
    material: material.name,
    tool: tool.name,
    adjustments: {
      featureSpecific: true,
      speedFactor: spindleSpeed / (baseCuttingSpeed * 1000 / (Math.PI * toolDiameter)),
      feedFactor: feedRate / (spindleSpeed * feedPerTooth * numberOfFlutes)
    }
  };
}

// 智能匹配材料和刀具
function matchMaterialAndTool(materialType, featureType, featureSize = {}) {
  const material = materialDatabase[materialType];
  if (!material) {
    throw new Error(`不支持的材料类型: ${materialType}`);
  }
  
  // 获取适合该材料和特征的刀具列表
  const suitableTools = [];
  
  for (const [toolKey, tool] of Object.entries(toolDatabase)) {
    // 检查刀具是否适用于该材料
    if (tool.materials.includes(materialType)) {
      // 获取适合该特征的刀具类型
      const featureTools = featureToToolMapping[featureType] || {};
      
      // 检查是否有该特征对应的刀具
      let hasFeatureTool = false;
      for (const featureTool in featureTools) {
        if (featureTools[featureTool].includes(materialType)) {
          hasFeatureTool = true;
          break;
        }
      }
      
      if (hasFeatureTool) {
        // 推荐加工参数
        const parameters = recommendMachiningParameters(materialType, toolKey, featureType, featureSize);
        
        suitableTools.push({
          toolType: toolKey,
          toolName: tool.name,
          parameters: parameters,
          ranking: calculateToolRanking(material, tool, featureType, featureSize)
        });
      }
    }
  }
  
  // 按排名排序
  suitableTools.sort((a, b) => b.ranking - a.ranking);
  
  return suitableTools;
}

// 计算刀具排名
function calculateToolRanking(material, tool, featureType, featureSize) {
  let ranking = 0;
  
  // 基础分
  ranking += 50;
  
  // 根据涂层加分
  if (tool.coating === 'AlCrN') ranking += 20;
  else if (tool.coating === 'TiCN') ranking += 15;
  
  // 根据最大切削速度加分
  ranking += (tool.maxCuttingSpeed / 100);
  
  // 根据材料硬度调整
  const materialHardness = (material.hardness.min + material.hardness.max) / 2;
  if (materialHardness > 400 && tool.maxCuttingSpeed > 300) ranking += 10;
  
  // 根据特征类型特殊加分
  if (featureType === 'thread' && tool.coating) ranking += 5;
  if (featureType === 'pocket' && tool.maxCuttingSpeed > 200) ranking += 5;
  
  return ranking;
}

// 获取材料列表
function getMaterialsList() {
  return Object.entries(materialDatabase).map(([key, value]) => ({
    key: key,
    name: value.name,
    properties: {
      hardness: value.hardness,
      tensileStrength: value.tensileStrength
    }
  }));
}

// 获取刀具列表
function getToolsList() {
  return Object.entries(toolDatabase).map(([key, value]) => ({
    key: key,
    name: value.name,
    properties: {
      coating: value.coating,
      maxRPM: value.maxRPM,
      maxCuttingSpeed: value.maxCuttingSpeed
    }
  }));
}

module.exports = {
  materialDatabase,
  toolDatabase,
  featureToToolMapping,
  recommendMachiningParameters,
  matchMaterialAndTool,
  getMaterialsList,
  getToolsList
};
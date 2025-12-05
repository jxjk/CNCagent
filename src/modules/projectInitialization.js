// src/modules/projectInitialization.js
// 项目初始化模块，负责创建和管理项目实例

const fs = require('fs');
const path = require('path');

// 项目类定义
class Project {
  constructor() {
    this.id = generateId();
    this.name = 'New Project';
    this.filePath = null;
    this.drawingInfo = null;
    this.geometryElements = [];
    this.dimensions = [];
    this.features = [];
    this.gCodeBlocks = [];
    this.createdAt = new Date();
    this.updatedAt = new Date();
    this.workspacePath = null;
  }

  updateMetadata() {
    this.updatedAt = new Date();
  }
}

// 生成唯一ID
function generateId() {
  return 'proj_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
}

// 初始化项目
function initializeProject(projectName = 'New Project') {
  if (typeof projectName !== 'string') {
    throw new Error('项目名必须是字符串');
  }

  const project = new Project();
  project.name = projectName;
  project.workspacePath = path.join(__dirname, '../../workspace', project.id);
  
  // 创建工作目录
  if (!fs.existsSync(project.workspacePath)) {
    fs.mkdirSync(project.workspacePath, { recursive: true });
  }
  
  return project;
}

// 清理工作区
function clearWorkspace() {
  const workspaceDir = path.join(__dirname, '../../workspace');
  if (fs.existsSync(workspaceDir)) {
    const projects = fs.readdirSync(workspaceDir);
    for (const projectDir of projects) {
      const fullPath = path.join(workspaceDir, projectDir);
      if (fs.statSync(fullPath).isDirectory()) {
        fs.rmSync(fullPath, { recursive: true, force: true });
      }
    }
  }
}

// 处理图纸导入
async function handleDrawingImport(filePath) {
  if (!filePath || typeof filePath !== 'string') {
    throw new Error('文件路径无效');
  }

  // 检查文件是否存在
  if (!fs.existsSync(filePath)) {
    throw new Error(`文件不存在: ${filePath}`);
  }

  // 模拟文件导入处理
  const fileExtension = path.extname(filePath).toLowerCase();
  const validExtensions = ['.pdf', '.dxf', '.svg', '.dwg', '.step', '.iges'];
  
  if (!validExtensions.includes(fileExtension)) {
    throw new Error(`不支持的文件格式: ${fileExtension}`);
  }

  // 创建项目实例
  const project = initializeProject(path.basename(filePath, fileExtension));
  project.filePath = filePath;
  project.updateMetadata();

  return project;
}

module.exports = {
  Project,
  initializeProject,
  clearWorkspace,
  handleDrawingImport
};
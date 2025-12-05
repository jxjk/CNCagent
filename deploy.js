const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// 部署CNCagent应用程序
function deployCNCagent() {
  console.log('开始部署CNCagent应用程序...');
  
  // 检查是否已安装PM2，如果没有则安装
  exec('npm list -g pm2', (error, stdout, stderr) => {
    if (error) {
      console.log('PM2未安装，正在全局安装PM2...');
      const installPM2 = spawn('npm', ['install', '-g', 'pm2'], { shell: true });
      
      installPM2.stdout.on('data', (data) => {
        console.log(`PM2安装输出: ${data}`);
      });
      
      installPM2.stderr.on('data', (data) => {
        console.error(`PM2安装错误: ${data}`);
      });
      
      installPM2.on('close', (code) => {
        if (code === 0) {
          console.log('PM2安装成功');
          startApplication();
        } else {
          console.error(`PM2安装失败，退出码: ${code}`);
          console.log('使用node直接启动应用...');
          startApplicationDirectly();
        }
      });
    } else {
      console.log('PM2已安装');
      startApplication();
    }
  });
}

function startApplication() {
  console.log('使用PM2启动CNCagent应用...');
  
  // 使用PM2启动应用
  const pm2Start = spawn('npx', ['pm2', 'start', 'src/index.js', '--name', 'cncagent', '--watch'], { shell: true });
  
  pm2Start.stdout.on('data', (data) => {
    console.log(`PM2启动输出: ${data}`);
  });
  
  pm2Start.stderr.on('data', (data) => {
    console.error(`PM2启动错误: ${data}`);
  });
  
  pm2Start.on('close', (code) => {
    if (code === 0) {
      console.log('CNCagent应用已通过PM2成功启动');
      checkApplicationStatus();
    } else {
      console.error(`PM2启动失败，退出码: ${code}`);
      console.log('尝试使用node直接启动应用...');
      startApplicationDirectly();
    }
  });
}

function startApplicationDirectly() {
  console.log('使用Node.js直接启动CNCagent应用...');
  
  // 直接使用Node.js启动应用
  const app = spawn('node', ['src/index.js'], { shell: true });
  
  app.stdout.on('data', (data) => {
    console.log(`应用输出: ${data}`);
  });
  
  app.stderr.on('data', (data) => {
    console.error(`应用错误: ${data}`);
  });
  
  app.on('close', (code) => {
    console.log(`应用进程已退出，退出码: ${code}`);
  });
}

function checkApplicationStatus() {
  console.log('检查应用状态...');
  
  setTimeout(() => {
    const pm2Status = spawn('npx', ['pm2', 'status'], { shell: true });
    
    pm2Status.stdout.on('data', (data) => {
      console.log('PM2状态信息:');
      console.log(data.toString());
    });
    
    pm2Status.stderr.on('data', (data) => {
      console.error(`PM2状态检查错误: ${data}`);
    });
    
    pm2Status.on('close', (code) => {
      console.log('应用状态检查完成');
      console.log('部署完成！CNCagent现在应该在 http://localhost:3000 上运行');
    });
  }, 5000); // 等待5秒让应用启动
}

// 确保在正确的目录下运行
process.chdir(path.join(__dirname));

// 执行部署
deployCNCagent();

module.exports = { deployCNCagent };
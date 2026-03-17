/**
 * PM2 Ecosystem Configuration - CLOUD Environment
 *
 * This config is for CLOUD deployment (Oracle VM, AWS, etc.)
 * Runs: cloud_orchestrator.py with embedded cloud watchers (Gmail, LinkedIn)
 *
 * ⚠️ CURRENTLY CONFIGURED FOR LOCAL TESTING
 * ⚠️ BEFORE CLOUD DEPLOYMENT: Update paths to match your cloud VM!
 *
 * Cloud VM paths example:
 *   cwd: '/home/ubuntu/ai-employee'
 *   VAULT_PATH: '/home/ubuntu/ai-employee/AI_Employee_Vault'
 *
 * Usage:
 *   pm2 start ecosystem.cloud.config.js
 *   pm2 save
 */

module.exports = {
  apps: [
    // =====================================================================
    // DEDUP API SERVER (runs on cloud, accessed by both local and cloud)
    // =====================================================================
    {
      name: 'ai-employee-dedup-api',
      script: './cloud/api_server.py',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',  // ⚠️ For cloud VM: /home/ubuntu/ai-employee
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env_file: '.env'  // Read DEDUP_API_PORT from .env
    },
    // =====================================================================
    // CLOUD AGENT (PM2 → cloud_orchestrator.py → cloud watchers)
    // =====================================================================
    {
      name: 'ai-employee-cloud',
      script: './cloud/cloud_orchestrator.py',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',  // ⚠️ For cloud VM: /home/ubuntu/ai-employee
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env_file: '.env',  // Read DEDUP_API_URL from .env
      env: {
        VAULT_PATH: '/mnt/d/coding Q4/hackathon-0/save-1/AI_Employee_Vault',  // ⚠️ For cloud VM: /home/ubuntu/ai-employee/AI_Employee_Vault
        AGENT_TYPE: 'cloud',
        LOG_LEVEL: 'INFO',
        NEEDS_ACTION_CHECK_INTERVAL: '30',
        GIT_SYNC_INTERVAL: '300'
      }
    }
  ]
};

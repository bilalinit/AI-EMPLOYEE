/**
 * PM2 Ecosystem Configuration - LOCAL Environment
 *
 * This config is for LOCAL development only.
 * Runs: watchdog.py → orchestrator.py → local watchers (Gmail, LinkedIn, FileSystem)
 *
 * Usage:
 *   pm2 start ecosystem.local.config.js
 *   pm2 save
 */

module.exports = {
  apps: [
    // =====================================================================
    // DEDUP API SERVER (needed for local testing)
    // =====================================================================
    {
      name: 'ai-employee-dedup-api',
      script: './cloud/api_server.py',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env_file: '.env'
    },
    // =====================================================================
    // LOCAL AGENT (PM2 → watchdog.py → orchestrator.py → local watchers)
    // =====================================================================
    {
      name: 'ai-employee-local',
      script: './watchdog.py',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env_file: '.env',  // Read DEDUP_API_URL from .env
      env: {
        VAULT_PATH: '/mnt/d/coding Q4/hackathon-0/save-1/AI_Employee_Vault',
        LOG_LEVEL: 'INFO',
        AGENT_TYPE: 'local'
      }
    }
  ]
};

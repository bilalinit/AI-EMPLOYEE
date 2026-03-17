/**
 * PM2 Ecosystem Configuration
 *
 * Process manager for AI Employee 24/7 operation.
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 save
 *   pm2 startup
 */

module.exports = {
  apps: [
    // =====================================================================
    // LOCAL AGENT (PM2 → watchdog.py → orchestrator.py → watchers)
    // =====================================================================
    {
      name: 'ai-employee-watchdog',
      script: './watchdog.py',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        VAULT_PATH: '/mnt/d/coding Q4/hackathon-0/save-1/AI_Employee_Vault',
        LOG_LEVEL: 'INFO'
      }
    },

    // =====================================================================
    // CLOUD AGENT (PM2 → cloud_orchestrator.py with watchers)
    // =====================================================================
    {
      name: 'ai-employee-cloud',
      script: './cloud/cloud_orchestrator.py',
      cwd: '/mnt/d/coding Q4/hackathon-0/save-1/ai_employee_scripts',
      interpreter: 'python3',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env_file: '.env',  // Load credentials from .env
      env: {
        VAULT_PATH: '/mnt/d/coding Q4/hackathon-0/save-1/AI_Employee_Vault',
        AGENT_TYPE: 'cloud',
        LOG_LEVEL: 'INFO',
        // Cloud agent intervals
        NEEDS_ACTION_CHECK_INTERVAL: '30',
        GIT_SYNC_INTERVAL: '300'
      }
    }
  ]
};

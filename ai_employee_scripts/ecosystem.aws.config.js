/**
 * PM2 Ecosystem Configuration - AWS Cloud Environment
 */

module.exports = {
  apps: [
    // =====================================================================
    // DEDUP API SERVER (runs on cloud, accessed by both local and cloud)
    // =====================================================================
    {
      name: 'ai-employee-dedup-api',
      script: '/home/ubuntu/.local/bin/uv',
      args: 'run python cloud/api_server.py',
      cwd: '/home/ubuntu/ai-employee/ai_employee_scripts',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        DEDUP_API_URL: 'http://localhost:5000',
        VAULT_PATH: '/home/ubuntu/ai-employee/AI_Employee_Vault'
      }
    },
    // =====================================================================
    // CLOUD AGENT (PM2 → cloud_orchestrator.py → cloud watchers)
    // =====================================================================
    {
      name: 'ai-employee-cloud',
      script: '/home/ubuntu/.local/bin/uv',
      args: 'run python cloud/cloud_orchestrator.py',
      cwd: '/home/ubuntu/ai-employee/ai_employee_scripts',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 5000,
      env: {
        DEDUP_API_URL: 'http://localhost:5000',
        VAULT_PATH: '/home/ubuntu/ai-employee/AI_Employee_Vault',
        AGENT_TYPE: 'cloud',
        CLOUD_ENV: 'true',
        LOG_LEVEL: 'INFO',
        NEEDS_ACTION_CHECK_INTERVAL: '30',
        GIT_SYNC_INTERVAL: '300'
      }
    }
  ]
};
